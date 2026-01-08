from __future__ import annotations

from enum import IntEnum
from pathlib import Path
import ctypes
import ctypes.util
import os
import sys

import certifi


class GitError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class ObjectType(IntEnum):
    ANY = -2
    INVALID = -1
    COMMIT = 1
    TREE = 2
    BLOB = 3
    TAG = 4


class SortMode(IntEnum):
    TOPOLOGICAL = 1 << 0
    TIME = 1 << 1
    REVERSE = 1 << 2


class FetchPrune(IntEnum):
    UNSPECIFIED = 0
    PRUNE = 1
    NO_PRUNE = 2


GIT_CHECKOUT_FORCE = 1 << 1
GIT_ITEROVER = -31
GIT_ENOTFOUND = -3
GIT_EUNBORNBRANCH = -9
GIT_OPT_SET_SSL_CERT_LOCATIONS = 12
GIT_STATUS_OPT_INCLUDE_UNTRACKED = 1 << 0
GIT_STATUS_OPT_RECURSE_UNTRACKED_DIRS = 1 << 4


class _GitOid(ctypes.Structure):
    _fields_ = [("id", ctypes.c_ubyte * 20)]


class _GitStrArray(ctypes.Structure):
    _fields_ = [
        ("strings", ctypes.POINTER(ctypes.c_char_p)),
        ("count", ctypes.c_size_t),
    ]


class _GitError(ctypes.Structure):
    _fields_ = [("message", ctypes.c_char_p), ("klass", ctypes.c_int)]


class _GitBuf(ctypes.Structure):
    _fields_ = [
        ("ptr", ctypes.c_char_p),
        ("reserved", ctypes.c_size_t),
        ("size", ctypes.c_size_t),
    ]


class _GitProxyOptions(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint),
        ("type", ctypes.c_int),
        ("url", ctypes.c_char_p),
        ("credentials", ctypes.c_void_p),
        ("certificate_check", ctypes.c_void_p),
        ("payload", ctypes.c_void_p),
    ]


class _GitRemoteCallbacks(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint),
        ("sideband_progress", ctypes.c_void_p),
        ("completion", ctypes.c_void_p),
        ("credentials", ctypes.c_void_p),
        ("certificate_check", ctypes.c_void_p),
        ("transfer_progress", ctypes.c_void_p),
        ("update_tips", ctypes.c_void_p),
        ("pack_progress", ctypes.c_void_p),
        ("push_transfer_progress", ctypes.c_void_p),
        ("push_update_reference", ctypes.c_void_p),
        ("push_negotiation", ctypes.c_void_p),
        ("transport", ctypes.c_void_p),
        ("remote_ready", ctypes.c_void_p),
        ("payload", ctypes.c_void_p),
        ("resolve_url", ctypes.c_void_p),
        ("update_refs", ctypes.c_void_p),
    ]


class _GitFetchOptions(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_int),
        ("callbacks", _GitRemoteCallbacks),
        ("prune", ctypes.c_int),
        ("update_fetchhead", ctypes.c_uint),
        ("download_tags", ctypes.c_int),
        ("proxy_opts", _GitProxyOptions),
        ("depth", ctypes.c_int),
        ("follow_redirects", ctypes.c_int),
        ("custom_headers", _GitStrArray),
    ]


class _GitPushOptions(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint),
        ("pb_parallelism", ctypes.c_uint),
        ("callbacks", _GitRemoteCallbacks),
        ("proxy_opts", _GitProxyOptions),
        ("follow_redirects", ctypes.c_int),
        ("custom_headers", _GitStrArray),
        ("remote_push_options", _GitStrArray),
    ]


class _GitCheckoutOptions(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint),
        ("checkout_strategy", ctypes.c_uint),
        ("disable_filters", ctypes.c_int),
        ("dir_mode", ctypes.c_uint),
        ("file_mode", ctypes.c_uint),
        ("file_open_flags", ctypes.c_int),
        ("notify_flags", ctypes.c_uint),
        ("notify_cb", ctypes.c_void_p),
        ("notify_payload", ctypes.c_void_p),
        ("progress_cb", ctypes.c_void_p),
        ("progress_payload", ctypes.c_void_p),
        ("paths", _GitStrArray),
        ("baseline", ctypes.c_void_p),
        ("baseline_index", ctypes.c_void_p),
        ("target_directory", ctypes.c_char_p),
        ("ancestor_label", ctypes.c_char_p),
        ("our_label", ctypes.c_char_p),
        ("their_label", ctypes.c_char_p),
        ("perfdata_cb", ctypes.c_void_p),
        ("perfdata_payload", ctypes.c_void_p),
    ]


class _GitCloneOptions(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint),
        ("checkout_opts", _GitCheckoutOptions),
        ("fetch_opts", _GitFetchOptions),
        ("bare", ctypes.c_int),
        ("local", ctypes.c_int),
        ("checkout_branch", ctypes.c_char_p),
        ("repository_cb", ctypes.c_void_p),
        ("repository_cb_payload", ctypes.c_void_p),
        ("remote_cb", ctypes.c_void_p),
        ("remote_cb_payload", ctypes.c_void_p),
    ]


class _GitStatusOptions(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint),
        ("show", ctypes.c_int),
        ("flags", ctypes.c_uint),
        ("pathspec", _GitStrArray),
        ("baseline", ctypes.c_void_p),
        ("rename_threshold", ctypes.c_uint16),
    ]


class _LibGit2:
    def __init__(self) -> None:
        self.lib = _load_library()
        self._bind()
        self._initialized = False

    def _bind(self) -> None:
        lib = self.lib

        lib.git_libgit2_init.restype = ctypes.c_int
        lib.git_libgit2_shutdown.restype = ctypes.c_int
        lib.git_libgit2_opts.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
        lib.git_libgit2_opts.restype = ctypes.c_int

        lib.git_error_last.argtypes = []
        lib.git_error_last.restype = ctypes.POINTER(_GitError)

        lib.git_repository_open.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_char_p,
        ]
        lib.git_repository_open.restype = ctypes.c_int
        lib.git_repository_init.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        lib.git_repository_init.restype = ctypes.c_int
        lib.git_repository_discover.argtypes = [
            ctypes.POINTER(_GitBuf),
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
        ]
        lib.git_repository_discover.restype = ctypes.c_int
        lib.git_repository_workdir.argtypes = [ctypes.c_void_p]
        lib.git_repository_workdir.restype = ctypes.c_char_p
        lib.git_repository_config.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
        ]
        lib.git_repository_config.restype = ctypes.c_int
        lib.git_repository_free.argtypes = [ctypes.c_void_p]
        lib.git_repository_free.restype = None
        lib.git_repository_head.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
        ]
        lib.git_repository_head.restype = ctypes.c_int
        lib.git_repository_head_unborn.argtypes = [ctypes.c_void_p]
        lib.git_repository_head_unborn.restype = ctypes.c_int
        lib.git_repository_set_head.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.git_repository_set_head.restype = ctypes.c_int
        lib.git_repository_set_head_detached.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_GitOid),
        ]
        lib.git_repository_set_head_detached.restype = ctypes.c_int
        lib.git_repository_index.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
        ]
        lib.git_repository_index.restype = ctypes.c_int

        lib.git_buf_dispose.argtypes = [ctypes.POINTER(_GitBuf)]
        lib.git_buf_dispose.restype = None

        lib.git_reference_lookup.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        lib.git_reference_lookup.restype = ctypes.c_int
        lib.git_reference_remove.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.git_reference_remove.restype = ctypes.c_int
        lib.git_reference_target.argtypes = [ctypes.c_void_p]
        lib.git_reference_target.restype = ctypes.POINTER(_GitOid)
        lib.git_reference_name.argtypes = [ctypes.c_void_p]
        lib.git_reference_name.restype = ctypes.c_char_p
        lib.git_reference_shorthand.argtypes = [ctypes.c_void_p]
        lib.git_reference_shorthand.restype = ctypes.c_char_p
        lib.git_reference_resolve.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
        ]
        lib.git_reference_resolve.restype = ctypes.c_int
        lib.git_reference_peel.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        lib.git_reference_peel.restype = ctypes.c_int
        lib.git_reference_free.argtypes = [ctypes.c_void_p]
        lib.git_reference_free.restype = None
        lib.git_reference_iterator_new.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
        ]
        lib.git_reference_iterator_new.restype = ctypes.c_int
        lib.git_reference_next_name.argtypes = [
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.c_void_p,
        ]
        lib.git_reference_next_name.restype = ctypes.c_int
        lib.git_reference_iterator_free.argtypes = [ctypes.c_void_p]
        lib.git_reference_iterator_free.restype = None

        lib.git_revparse_single.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        lib.git_revparse_single.restype = ctypes.c_int

        lib.git_object_lookup.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.POINTER(_GitOid),
            ctypes.c_int,
        ]
        lib.git_object_lookup.restype = ctypes.c_int
        lib.git_object_id.argtypes = [ctypes.c_void_p]
        lib.git_object_id.restype = ctypes.POINTER(_GitOid)
        lib.git_object_type.argtypes = [ctypes.c_void_p]
        lib.git_object_type.restype = ctypes.c_int
        lib.git_object_peel.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        lib.git_object_peel.restype = ctypes.c_int
        lib.git_object_free.argtypes = [ctypes.c_void_p]
        lib.git_object_free.restype = None

        lib.git_commit_lookup.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.POINTER(_GitOid),
        ]
        lib.git_commit_lookup.restype = ctypes.c_int
        lib.git_commit_id.argtypes = [ctypes.c_void_p]
        lib.git_commit_id.restype = ctypes.POINTER(_GitOid)
        lib.git_commit_message.argtypes = [ctypes.c_void_p]
        lib.git_commit_message.restype = ctypes.c_char_p
        lib.git_commit_message_raw.argtypes = [ctypes.c_void_p]
        lib.git_commit_message_raw.restype = ctypes.c_char_p
        lib.git_commit_message_encoding.argtypes = [ctypes.c_void_p]
        lib.git_commit_message_encoding.restype = ctypes.c_char_p
        lib.git_commit_free.argtypes = [ctypes.c_void_p]
        lib.git_commit_free.restype = None

        lib.git_tag_lookup.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.POINTER(_GitOid),
        ]
        lib.git_tag_lookup.restype = ctypes.c_int
        lib.git_tag_target.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
        lib.git_tag_target.restype = ctypes.c_int
        lib.git_tag_target_id.argtypes = [ctypes.c_void_p]
        lib.git_tag_target_id.restype = ctypes.POINTER(_GitOid)
        lib.git_tag_free.argtypes = [ctypes.c_void_p]
        lib.git_tag_free.restype = None

        lib.git_tree_lookup.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.POINTER(_GitOid),
        ]
        lib.git_tree_lookup.restype = ctypes.c_int
        lib.git_tree_free.argtypes = [ctypes.c_void_p]
        lib.git_tree_free.restype = None

        lib.git_oid_fromstr.argtypes = [ctypes.POINTER(_GitOid), ctypes.c_char_p]
        lib.git_oid_fromstr.restype = ctypes.c_int
        lib.git_oid_tostr_s.argtypes = [ctypes.POINTER(_GitOid)]
        lib.git_oid_tostr_s.restype = ctypes.c_char_p

        lib.git_signature_new.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_long,
            ctypes.c_int,
        ]
        lib.git_signature_new.restype = ctypes.c_int
        lib.git_signature_default.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
        ]
        lib.git_signature_default.restype = ctypes.c_int
        lib.git_signature_free.argtypes = [ctypes.c_void_p]
        lib.git_signature_free.restype = None

        lib.git_commit_create.argtypes = [
            ctypes.POINTER(_GitOid),
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        lib.git_commit_create.restype = ctypes.c_int
        lib.git_commit_create_from_ids.argtypes = [
            ctypes.POINTER(_GitOid),
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(_GitOid),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.POINTER(_GitOid)),
        ]
        lib.git_commit_create_from_ids.restype = ctypes.c_int

        lib.git_tag_create.argtypes = [
            ctypes.POINTER(_GitOid),
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        lib.git_tag_create.restype = ctypes.c_int

        lib.git_index_add_all.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_GitStrArray),
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        lib.git_index_add_all.restype = ctypes.c_int
        lib.git_index_write_tree.argtypes = [ctypes.POINTER(_GitOid), ctypes.c_void_p]
        lib.git_index_write_tree.restype = ctypes.c_int
        lib.git_index_write.argtypes = [ctypes.c_void_p]
        lib.git_index_write.restype = ctypes.c_int
        lib.git_index_free.argtypes = [ctypes.c_void_p]
        lib.git_index_free.restype = None

        lib.git_revwalk_new.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
        ]
        lib.git_revwalk_new.restype = ctypes.c_int
        lib.git_revwalk_push.argtypes = [ctypes.c_void_p, ctypes.POINTER(_GitOid)]
        lib.git_revwalk_push.restype = ctypes.c_int
        lib.git_revwalk_hide.argtypes = [ctypes.c_void_p, ctypes.POINTER(_GitOid)]
        lib.git_revwalk_hide.restype = ctypes.c_int
        lib.git_revwalk_next.argtypes = [ctypes.POINTER(_GitOid), ctypes.c_void_p]
        lib.git_revwalk_next.restype = ctypes.c_int
        lib.git_revwalk_sorting.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        lib.git_revwalk_sorting.restype = None
        lib.git_revwalk_free.argtypes = [ctypes.c_void_p]
        lib.git_revwalk_free.restype = None

        lib.git_graph_descendant_of.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_GitOid),
            ctypes.POINTER(_GitOid),
        ]
        lib.git_graph_descendant_of.restype = ctypes.c_int
        lib.git_merge_base.argtypes = [
            ctypes.POINTER(_GitOid),
            ctypes.c_void_p,
            ctypes.POINTER(_GitOid),
            ctypes.POINTER(_GitOid),
        ]
        lib.git_merge_base.restype = ctypes.c_int

        lib.git_checkout_head.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_GitCheckoutOptions),
        ]
        lib.git_checkout_head.restype = ctypes.c_int
        lib.git_checkout_tree.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(_GitCheckoutOptions),
        ]
        lib.git_checkout_tree.restype = ctypes.c_int
        lib.git_checkout_options_init.argtypes = [
            ctypes.POINTER(_GitCheckoutOptions),
            ctypes.c_uint,
        ]
        lib.git_checkout_options_init.restype = ctypes.c_int

        lib.git_status_options_init.argtypes = [
            ctypes.POINTER(_GitStatusOptions),
            ctypes.c_uint,
        ]
        lib.git_status_options_init.restype = ctypes.c_int
        lib.git_status_list_new.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.POINTER(_GitStatusOptions),
        ]
        lib.git_status_list_new.restype = ctypes.c_int
        lib.git_status_list_entrycount.argtypes = [ctypes.c_void_p]
        lib.git_status_list_entrycount.restype = ctypes.c_size_t
        lib.git_status_list_free.argtypes = [ctypes.c_void_p]
        lib.git_status_list_free.restype = None
        lib.git_config_delete_multivar.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        lib.git_config_delete_multivar.restype = ctypes.c_int
        lib.git_config_free.argtypes = [ctypes.c_void_p]
        lib.git_config_free.restype = None

        lib.git_remote_lookup.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        lib.git_remote_lookup.restype = ctypes.c_int
        lib.git_remote_create_anonymous.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        lib.git_remote_create_anonymous.restype = ctypes.c_int
        lib.git_remote_fetch.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_GitStrArray),
            ctypes.POINTER(_GitFetchOptions),
            ctypes.c_char_p,
        ]
        lib.git_remote_fetch.restype = ctypes.c_int
        lib.git_remote_push.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_GitStrArray),
            ctypes.POINTER(_GitPushOptions),
        ]
        lib.git_remote_push.restype = ctypes.c_int
        lib.git_remote_free.argtypes = [ctypes.c_void_p]
        lib.git_remote_free.restype = None

        lib.git_fetch_options_init.argtypes = [
            ctypes.POINTER(_GitFetchOptions),
            ctypes.c_uint,
        ]
        lib.git_fetch_options_init.restype = ctypes.c_int
        lib.git_push_options_init.argtypes = [
            ctypes.POINTER(_GitPushOptions),
            ctypes.c_uint,
        ]
        lib.git_push_options_init.restype = ctypes.c_int
        lib.git_clone_options_init.argtypes = [
            ctypes.POINTER(_GitCloneOptions),
            ctypes.c_uint,
        ]
        lib.git_clone_options_init.restype = ctypes.c_int
        lib.git_clone.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.POINTER(_GitCloneOptions),
        ]
        lib.git_clone.restype = ctypes.c_int

    def ensure_initialized(self) -> None:
        if self._initialized:
            return
        _check(self.lib.git_libgit2_init())
        ca_path = (
            os.environ.get("GIT_SSL_CAINFO")
            or os.environ.get("SSL_CERT_FILE")
            or certifi.where()
        ).encode()
        _check(self.lib.git_libgit2_opts(GIT_OPT_SET_SSL_CERT_LOCATIONS, ca_path, None))
        self._initialized = True


def _load_library() -> ctypes.CDLL:
    base = Path(__file__).resolve().parent / "lib"
    candidates: list[str] = []
    if sys.platform.startswith("linux"):
        candidates.append(str(base / "libgirokmoji_native.so"))
    elif sys.platform == "darwin":
        candidates.append(str(base / "libgirokmoji_native.dylib"))
    elif os.name == "nt":
        candidates.append(str(base / "girokmoji_native.dll"))

    for path in candidates:
        if os.path.exists(path):
            return ctypes.CDLL(path)

    for name in ("girokmoji_native", "git2"):
        found = ctypes.util.find_library(name)
        if found:
            return ctypes.CDLL(found)

    raise RuntimeError("libgit2 shared library not found")


_LIB = _LibGit2()


def _check(code: int) -> None:
    if code >= 0:
        return
    err = _LIB.lib.git_error_last()
    if err and err.contents.message:
        message = err.contents.message.decode()
    else:
        message = "libgit2 error"
    raise GitError(message, code)


def _oid_from_hex(hex_str: str) -> _GitOid:
    oid = _GitOid()
    _check(_LIB.lib.git_oid_fromstr(ctypes.byref(oid), hex_str.encode()))
    return oid


def _oid_to_hex(oid_ptr: ctypes._Pointer[_GitOid]) -> str:
    if not oid_ptr:
        raise GitError("missing oid")
    text = _LIB.lib.git_oid_tostr_s(oid_ptr)
    if not text:
        raise GitError("oid conversion failed")
    return ctypes.string_at(text).decode()


def _copy_oid(oid_ptr: ctypes._Pointer[_GitOid]) -> _GitOid:
    if not oid_ptr:
        raise GitError("missing oid")
    oid = _GitOid()
    ctypes.memmove(ctypes.byref(oid), oid_ptr, ctypes.sizeof(_GitOid))
    return oid


def _make_strarray(values: list[str] | None) -> tuple[_GitStrArray, ctypes.Array]:
    if not values:
        arr = (_GitStrArray)(None, 0)
        return arr, (ctypes.c_char_p * 1)()
    encoded = [v.encode() for v in values]
    array = (ctypes.c_char_p * len(encoded))(*encoded)
    return _GitStrArray(array, len(encoded)), array


class Oid:
    def __init__(self, hex_str: str):
        self._hex = hex_str

    def __str__(self) -> str:
        return self._hex

    def __repr__(self) -> str:
        return f"Oid('{self._hex}')"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Oid):
            return self._hex == other._hex
        if isinstance(other, str):
            return self._hex == other
        return False

    @property
    def hex(self) -> str:
        return self._hex

    @classmethod
    def from_ptr(cls, oid_ptr: ctypes._Pointer[_GitOid]) -> "Oid":
        return cls(_oid_to_hex(oid_ptr))


class Signature:
    def __init__(self, name: str, email: str):
        _LIB.ensure_initialized()
        sig = ctypes.c_void_p()
        _check(
            _LIB.lib.git_signature_new(
                ctypes.byref(sig), name.encode(), email.encode(), 0, 0
            )
        )
        self._ptr = sig

    @classmethod
    def _from_ptr(cls, ptr: ctypes.c_void_p) -> "Signature":
        obj = cls.__new__(cls)
        obj._ptr = ptr
        return obj

    @property
    def _as_ptr(self) -> ctypes.c_void_p:
        return self._ptr

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_signature_free(ptr)


class _GitObject:
    def __init__(self, ptr: ctypes.c_void_p, obj_type: int):
        self._ptr = ptr
        self._type = obj_type

    @property
    def id(self) -> Oid:
        oid_ptr = _LIB.lib.git_object_id(self._ptr)
        return Oid.from_ptr(oid_ptr)

    def peel(self, target_type: ObjectType) -> "Commit":
        out = ctypes.c_void_p()
        _check(_LIB.lib.git_object_peel(ctypes.byref(out), self._ptr, int(target_type)))
        return Commit(out)

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_object_free(ptr)


class Commit(_GitObject):
    def __init__(self, ptr: ctypes.c_void_p):
        super().__init__(ptr, ObjectType.COMMIT)

    @property
    def message(self) -> str | None:
        msg = _LIB.lib.git_commit_message(self._ptr)
        if not msg:
            return None
        return ctypes.string_at(msg).decode()

    @property
    def raw_message(self) -> bytes:
        msg = _LIB.lib.git_commit_message_raw(self._ptr)
        if not msg:
            return b""
        return ctypes.string_at(msg)

    @property
    def message_encoding(self) -> str:
        enc = _LIB.lib.git_commit_message_encoding(self._ptr)
        if not enc:
            return "utf-8"
        return ctypes.string_at(enc).decode()

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_commit_free(ptr)


class Tag(_GitObject):
    def __init__(self, ptr: ctypes.c_void_p):
        super().__init__(ptr, ObjectType.TAG)

    def peel(self, target_type: ObjectType) -> "Commit":
        out = ctypes.c_void_p()
        _check(_LIB.lib.git_tag_target(ctypes.byref(out), self._ptr))
        peeled = ctypes.c_void_p()
        _check(_LIB.lib.git_object_peel(ctypes.byref(peeled), out, int(target_type)))
        _LIB.lib.git_object_free(out)
        return Commit(peeled)

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_tag_free(ptr)


class Reference:
    def __init__(self, ptr: ctypes.c_void_p):
        self._ptr = ptr

    @property
    def name(self) -> str:
        name = _LIB.lib.git_reference_name(self._ptr)
        return ctypes.string_at(name).decode()

    @property
    def shorthand(self) -> str:
        short = _LIB.lib.git_reference_shorthand(self._ptr)
        if not short:
            return ""
        return ctypes.string_at(short).decode()

    @property
    def target(self) -> Oid | None:
        oid_ptr = _LIB.lib.git_reference_target(self._ptr)
        if oid_ptr:
            return Oid.from_ptr(oid_ptr)
        resolved = ctypes.c_void_p()
        code = _LIB.lib.git_reference_resolve(ctypes.byref(resolved), self._ptr)
        if code < 0:
            return None
        try:
            oid_ptr = _LIB.lib.git_reference_target(resolved)
            if not oid_ptr:
                return None
            return Oid.from_ptr(oid_ptr)
        finally:
            _LIB.lib.git_reference_free(resolved)

    def resolve(self) -> "Reference":
        out = ctypes.c_void_p()
        _check(_LIB.lib.git_reference_resolve(ctypes.byref(out), self._ptr))
        return Reference(out)

    def peel(self, target_type: ObjectType) -> "_GitObject":
        obj = ctypes.c_void_p()
        _check(
            _LIB.lib.git_reference_peel(ctypes.byref(obj), self._ptr, int(target_type))
        )
        return _wrap_object(obj)

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_reference_free(ptr)


class Config:
    def __init__(self, ptr: ctypes.c_void_p):
        self._ptr = ptr

    def delete_multivar(self, name: str, regex: str) -> None:
        code = _LIB.lib.git_config_delete_multivar(
            self._ptr, name.encode(), regex.encode()
        )
        if code == GIT_ENOTFOUND:
            return
        _check(code)

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_config_free(ptr)


class References:
    def __init__(self, repo: "Repository"):
        self._repo = repo

    def get(self, name: str) -> Reference | None:
        ref = ctypes.c_void_p()
        code = _LIB.lib.git_reference_lookup(
            ctypes.byref(ref), self._repo._ptr, name.encode()
        )
        if code == GIT_ENOTFOUND:
            return None
        _check(code)
        return Reference(ref)

    def delete(self, name: str) -> None:
        code = _LIB.lib.git_reference_remove(self._repo._ptr, name.encode())
        if code == GIT_ENOTFOUND:
            raise KeyError(name)
        _check(code)

    def __iter__(self):
        it = ctypes.c_void_p()
        _check(_LIB.lib.git_reference_iterator_new(ctypes.byref(it), self._repo._ptr))
        try:
            while True:
                out = ctypes.c_char_p()
                code = _LIB.lib.git_reference_next_name(ctypes.byref(out), it)
                if code == GIT_ITEROVER:
                    break
                _check(code)
                if out:
                    yield ctypes.string_at(out).decode()
        finally:
            _LIB.lib.git_reference_iterator_free(it)


class Index:
    def __init__(self, ptr: ctypes.c_void_p):
        self._ptr = ptr

    def add_all(self) -> None:
        _check(_LIB.lib.git_index_add_all(self._ptr, None, 0, None, None))

    def write(self) -> None:
        _check(_LIB.lib.git_index_write(self._ptr))

    def write_tree(self) -> Oid:
        oid = _GitOid()
        _check(_LIB.lib.git_index_write_tree(ctypes.byref(oid), self._ptr))
        return Oid.from_ptr(ctypes.pointer(oid))

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_index_free(ptr)


class RevWalk:
    def __init__(self, repo: "Repository", start: Oid):
        out = ctypes.c_void_p()
        _check(_LIB.lib.git_revwalk_new(ctypes.byref(out), repo._ptr))
        self._ptr = out
        self._repo = repo
        _check(
            _LIB.lib.git_revwalk_push(self._ptr, ctypes.byref(self._resolve_oid(start)))
        )

    def _resolve_oid(self, oid: Oid) -> _GitOid:
        obj = ctypes.c_void_p()
        _check(
            _LIB.lib.git_object_lookup(
                ctypes.byref(obj),
                self._repo._ptr,
                ctypes.byref(_oid_from_hex(oid.hex)),
                int(ObjectType.ANY),
            )
        )
        try:
            obj_type = _LIB.lib.git_object_type(obj)
            if obj_type != ObjectType.COMMIT:
                peeled = ctypes.c_void_p()
                _check(
                    _LIB.lib.git_object_peel(
                        ctypes.byref(peeled), obj, int(ObjectType.COMMIT)
                    )
                )
                try:
                    return _copy_oid(_LIB.lib.git_object_id(peeled))
                finally:
                    _LIB.lib.git_object_free(peeled)
            return _copy_oid(_LIB.lib.git_object_id(obj))
        finally:
            _LIB.lib.git_object_free(obj)

    def hide(self, oid: Oid) -> None:
        _check(
            _LIB.lib.git_revwalk_hide(self._ptr, ctypes.byref(self._resolve_oid(oid)))
        )

    def sorting(self, mode: int) -> None:
        _LIB.lib.git_revwalk_sorting(self._ptr, mode)

    def __iter__(self):
        oid = _GitOid()
        while True:
            code = _LIB.lib.git_revwalk_next(ctypes.byref(oid), self._ptr)
            if code == GIT_ITEROVER:
                break
            _check(code)
            commit_ptr = ctypes.c_void_p()
            _check(
                _LIB.lib.git_commit_lookup(
                    ctypes.byref(commit_ptr), self._repo._ptr, ctypes.byref(oid)
                )
            )
            yield Commit(commit_ptr)

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_revwalk_free(ptr)


class Remote:
    def __init__(self, ptr: ctypes.c_void_p):
        self._ptr = ptr

    def fetch(
        self,
        refspecs: list[str] | None = None,
        prune: int | None = None,
        depth: int = 0,
    ) -> None:
        opts = _GitFetchOptions()
        _check(_LIB.lib.git_fetch_options_init(ctypes.byref(opts), 1))
        if prune is not None:
            opts.prune = int(prune)
        if depth:
            opts.depth = int(depth)
        refspec_arr, backing = _make_strarray(refspecs)
        _check(
            _LIB.lib.git_remote_fetch(
                self._ptr,
                ctypes.byref(refspec_arr) if refspecs else None,
                ctypes.byref(opts),
                None,
            )
        )
        _ = backing

    def push(self, refspecs: list[str]) -> None:
        opts = _GitPushOptions()
        _check(_LIB.lib.git_push_options_init(ctypes.byref(opts), 1))
        refspec_arr, backing = _make_strarray(refspecs)
        _check(
            _LIB.lib.git_remote_push(
                self._ptr, ctypes.byref(refspec_arr), ctypes.byref(opts)
            )
        )
        _ = backing

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_remote_free(ptr)


class RemoteCollection:
    def __init__(self, repo: "Repository"):
        self._repo = repo

    def __getitem__(self, name: str) -> Remote:
        remote = ctypes.c_void_p()
        code = _LIB.lib.git_remote_lookup(
            ctypes.byref(remote), self._repo._ptr, name.encode()
        )
        if code == GIT_ENOTFOUND:
            raise KeyError(name)
        _check(code)
        return Remote(remote)

    def create_anonymous(self, url: str) -> Remote:
        remote = ctypes.c_void_p()
        _check(
            _LIB.lib.git_remote_create_anonymous(
                ctypes.byref(remote), self._repo._ptr, url.encode()
            )
        )
        return Remote(remote)


class Repository:
    def __init__(self, path: str | Path):
        _LIB.ensure_initialized()
        repo = ctypes.c_void_p()
        code = _LIB.lib.git_repository_open(
            ctypes.byref(repo), os.fsencode(os.fspath(path))
        )
        if code < 0:
            raise GitError(_error_message(code), code)
        self._ptr = repo

    @classmethod
    def _from_ptr(cls, ptr: ctypes.c_void_p) -> "Repository":
        obj = cls.__new__(cls)
        obj._ptr = ptr
        return obj

    @property
    def workdir(self) -> str:
        path = _LIB.lib.git_repository_workdir(self._ptr)
        if not path:
            return ""
        return ctypes.string_at(path).decode()

    @property
    def config(self) -> "Config":
        cfg = ctypes.c_void_p()
        _check(_LIB.lib.git_repository_config(ctypes.byref(cfg), self._ptr))
        return Config(cfg)

    @property
    def index(self) -> Index:
        idx = ctypes.c_void_p()
        _check(_LIB.lib.git_repository_index(ctypes.byref(idx), self._ptr))
        return Index(idx)

    @property
    def head(self) -> Reference | None:
        ref = ctypes.c_void_p()
        code = _LIB.lib.git_repository_head(ctypes.byref(ref), self._ptr)
        if code == GIT_EUNBORNBRANCH:
            return None
        _check(code)
        return Reference(ref)

    @property
    def head_is_unborn(self) -> bool:
        return bool(_LIB.lib.git_repository_head_unborn(self._ptr))

    @property
    def references(self) -> References:
        return References(self)

    @property
    def remotes(self) -> RemoteCollection:
        return RemoteCollection(self)

    @property
    def default_signature(self) -> Signature:
        sig = ctypes.c_void_p()
        code = _LIB.lib.git_signature_default(ctypes.byref(sig), self._ptr)
        if code < 0:
            raise KeyError("default signature unavailable")
        return Signature._from_ptr(sig)

    def status(self):
        opts = _GitStatusOptions()
        _check(_LIB.lib.git_status_options_init(ctypes.byref(opts), 1))
        opts.flags = (
            GIT_STATUS_OPT_INCLUDE_UNTRACKED | GIT_STATUS_OPT_RECURSE_UNTRACKED_DIRS
        )
        status_list = ctypes.c_void_p()
        _check(
            _LIB.lib.git_status_list_new(
                ctypes.byref(status_list), self._ptr, ctypes.byref(opts)
            )
        )
        try:
            count = _LIB.lib.git_status_list_entrycount(status_list)
        finally:
            _LIB.lib.git_status_list_free(status_list)
        return [None] * count

    def walk(self, oid: Oid) -> RevWalk:
        return RevWalk(self, oid)

    def descendant_of(self, commit: Oid, ancestor: Oid) -> bool:
        return (
            _LIB.lib.git_graph_descendant_of(
                self._ptr,
                ctypes.byref(_oid_from_hex(commit.hex)),
                ctypes.byref(_oid_from_hex(ancestor.hex)),
            )
            == 1
        )

    def merge_base(self, left: Oid, right: Oid) -> Oid | None:
        out = _GitOid()
        code = _LIB.lib.git_merge_base(
            ctypes.byref(out),
            self._ptr,
            ctypes.byref(_oid_from_hex(left.hex)),
            ctypes.byref(_oid_from_hex(right.hex)),
        )
        if code == GIT_ENOTFOUND:
            return None
        _check(code)
        return Oid.from_ptr(ctypes.pointer(out))

    def revparse_single(self, spec: str):
        obj = ctypes.c_void_p()
        _check(
            _LIB.lib.git_revparse_single(ctypes.byref(obj), self._ptr, spec.encode())
        )
        return _wrap_object(obj)

    def lookup_reference(self, name: str) -> Reference:
        ref = ctypes.c_void_p()
        code = _LIB.lib.git_reference_lookup(
            ctypes.byref(ref), self._ptr, name.encode()
        )
        if code == GIT_ENOTFOUND:
            raise KeyError(name)
        _check(code)
        return Reference(ref)

    def create_commit(
        self,
        refname: str,
        author: Signature,
        committer: Signature,
        message: str,
        tree_oid: Oid,
        parents: list[Oid | Commit],
    ) -> Oid:
        tree = _oid_from_hex(tree_oid.hex)
        parent_oids = [
            _oid_from_hex(parent.id.hex if isinstance(parent, Commit) else parent.hex)
            for parent in parents
        ]
        parent_ptrs = (ctypes.POINTER(_GitOid) * len(parent_oids))()
        for i, oid in enumerate(parent_oids):
            parent_ptrs[i] = ctypes.pointer(oid)
        out = _GitOid()
        _check(
            _LIB.lib.git_commit_create_from_ids(
                ctypes.byref(out),
                self._ptr,
                refname.encode(),
                author._as_ptr,
                committer._as_ptr,
                None,
                message.encode(),
                ctypes.byref(tree),
                len(parent_oids),
                parent_ptrs if parent_oids else None,
            )
        )
        return Oid.from_ptr(ctypes.pointer(out))

    def create_tag(
        self,
        name: str,
        target: Oid,
        target_type: ObjectType,
        tagger: Signature,
        message: str,
    ) -> Oid:
        obj = ctypes.c_void_p()
        _check(
            _LIB.lib.git_object_lookup(
                ctypes.byref(obj),
                self._ptr,
                ctypes.byref(_oid_from_hex(target.hex)),
                int(target_type),
            )
        )
        out = _GitOid()
        _check(
            _LIB.lib.git_tag_create(
                ctypes.byref(out),
                self._ptr,
                name.encode(),
                obj,
                tagger._as_ptr,
                message.encode(),
                0,
            )
        )
        _LIB.lib.git_object_free(obj)
        return Oid.from_ptr(ctypes.pointer(out))

    def checkout_head(self, *, strategy: int = GIT_CHECKOUT_FORCE) -> None:
        opts = _GitCheckoutOptions()
        _check(_LIB.lib.git_checkout_options_init(ctypes.byref(opts), 1))
        opts.checkout_strategy = strategy
        _check(_LIB.lib.git_checkout_head(self._ptr, ctypes.byref(opts)))

    def checkout_tree(
        self, target: _GitObject, *, strategy: int = GIT_CHECKOUT_FORCE
    ) -> None:
        opts = _GitCheckoutOptions()
        _check(_LIB.lib.git_checkout_options_init(ctypes.byref(opts), 1))
        opts.checkout_strategy = strategy
        _check(_LIB.lib.git_checkout_tree(self._ptr, target._ptr, ctypes.byref(opts)))

    def set_head(self, target: Oid | str) -> None:
        if isinstance(target, Oid):
            _check(
                _LIB.lib.git_repository_set_head_detached(
                    self._ptr, ctypes.byref(_oid_from_hex(target.hex))
                )
            )
            return
        _check(_LIB.lib.git_repository_set_head(self._ptr, target.encode()))

    def __getitem__(self, oid: Oid) -> _GitObject:
        obj = ctypes.c_void_p()
        _check(
            _LIB.lib.git_object_lookup(
                ctypes.byref(obj),
                self._ptr,
                ctypes.byref(_oid_from_hex(oid.hex)),
                int(ObjectType.ANY),
            )
        )
        return _wrap_object(obj)

    def __del__(self) -> None:
        ptr = getattr(self, "_ptr", None)
        if ptr:
            _LIB.lib.git_repository_free(ptr)


def _wrap_object(obj: ctypes.c_void_p) -> _GitObject:
    obj_type = _LIB.lib.git_object_type(obj)
    if obj_type == ObjectType.COMMIT:
        return Commit(obj)
    if obj_type == ObjectType.TAG:
        return Tag(obj)
    return _GitObject(obj, obj_type)


def _error_message(code: int) -> str:
    err = _LIB.lib.git_error_last()
    if err and err.contents.message:
        return err.contents.message.decode()
    return f"libgit2 error ({code})"


def init_repository(path: str | Path) -> Repository:
    _LIB.ensure_initialized()
    repo = ctypes.c_void_p()
    _check(
        _LIB.lib.git_repository_init(
            ctypes.byref(repo), os.fsencode(os.fspath(path)), 0
        )
    )
    return Repository._from_ptr(repo)


def discover_repository(path: str | Path) -> str | None:
    _LIB.ensure_initialized()
    buf = _GitBuf(None, 0, 0)
    code = _LIB.lib.git_repository_discover(
        ctypes.byref(buf), os.fsencode(os.fspath(path)), 0, None
    )
    if code < 0:
        return None
    try:
        return ctypes.string_at(buf.ptr).decode()
    finally:
        _LIB.lib.git_buf_dispose(ctypes.byref(buf))


def clone_repository(
    url: str, path: str | Path, checkout_branch: str | None = None, depth: int = 0
) -> Repository:
    _LIB.ensure_initialized()
    opts = _GitCloneOptions()
    _check(_LIB.lib.git_clone_options_init(ctypes.byref(opts), 1))
    if checkout_branch:
        opts.checkout_branch = checkout_branch.encode()
    if depth:
        opts.fetch_opts.depth = int(depth)
    repo = ctypes.c_void_p()
    _check(
        _LIB.lib.git_clone(
            ctypes.byref(repo),
            url.encode(),
            os.fsencode(os.fspath(path)),
            ctypes.byref(opts),
        )
    )
    return Repository._from_ptr(repo)


__all__ = [
    "Commit",
    "FetchPrune",
    "GitError",
    "GIT_CHECKOUT_FORCE",
    "ObjectType",
    "Oid",
    "Reference",
    "Repository",
    "Signature",
    "SortMode",
    "Tag",
    "clone_repository",
    "discover_repository",
    "init_repository",
]
