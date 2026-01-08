const std = @import("std");

const CmakeProject = struct {
    configure: *std.Build.Step.Run,
    build: *std.Build.Step.Run,
    install: *std.Build.Step.Run,
};

fn add_cmake_project(
    b: *std.Build,
    source_dir: []const u8,
    build_dir: []const u8,
    install_prefix: []const u8,
    build_type: []const u8,
    cc_cmd: []const u8,
    extra_args: []const []const u8,
) CmakeProject {
    const configure = b.addSystemCommand(&.{
        "cmake",
        "-S",
        source_dir,
        "-B",
        build_dir,
        b.fmt("-DCMAKE_BUILD_TYPE={s}", .{build_type}),
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        b.fmt("-DCMAKE_INSTALL_PREFIX={s}", .{install_prefix}),
        "-DCMAKE_INSTALL_LIBDIR=lib",
        "-DCMAKE_INSTALL_BINDIR=lib",
    });

    for (extra_args) |arg| {
        configure.addArg(arg);
    }

    configure.setEnvironmentVariable("CC", cc_cmd);
    configure.setEnvironmentVariable("AR", "zig ar");
    configure.setEnvironmentVariable("RANLIB", "zig ranlib");

    const build_step = b.addSystemCommand(&.{
        "cmake",
        "--build",
        build_dir,
        "--config",
        build_type,
    });
    build_step.step.dependOn(&configure.step);

    const install = b.addSystemCommand(&.{
        "cmake",
        "--install",
        build_dir,
        "--config",
        build_type,
    });
    install.step.dependOn(&build_step.step);

    return .{
        .configure = configure,
        .build = build_step,
        .install = install,
    };
}

pub fn build(b: *std.Build) void {
    const optimize = b.standardOptimizeOption(.{});
    _ = b.standardTargetOptions(.{});

    const build_type = switch (optimize) {
        .Debug => "Debug",
        else => "Release",
    };

    const deps_prefix = b.pathFromRoot("build/native/deps");
    const cc_cmd = "zig cc";
    const cc_launcher = b.pathFromRoot("scripts/zig-cc-wrapper.py");

    const mbedtls = add_cmake_project(
        b,
        "vendor/mbedtls",
        "build/native/mbedtls",
        deps_prefix,
        build_type,
        cc_cmd,
        &.{
            b.fmt("-DCMAKE_C_COMPILER_LAUNCHER={s}", .{cc_launcher}),
            b.fmt("-DCMAKE_C_LINKER_LAUNCHER={s}", .{cc_launcher}),
            "-DENABLE_TESTING=OFF",
            "-DENABLE_PROGRAMS=OFF",
            "-DBUILD_SHARED_LIBS=OFF",
        },
    );

    const zlib = add_cmake_project(
        b,
        "vendor/zlib",
        "build/native/zlib",
        deps_prefix,
        build_type,
        cc_cmd,
        &.{
            b.fmt("-DCMAKE_C_COMPILER_LAUNCHER={s}", .{cc_launcher}),
            b.fmt("-DCMAKE_C_LINKER_LAUNCHER={s}", .{cc_launcher}),
            "-DZLIB_BUILD_SHARED=OFF",
            "-DZLIB_BUILD_STATIC=ON",
            "-DZLIB_BUILD_TESTING=OFF",
            "-DZLIB_BUILD_MINIZIP=OFF",
        },
    );

    const libgit2_shim = b.pathFromRoot("girokmoji/native/include");
    const libgit2 = add_cmake_project(
        b,
        "vendor/libgit2",
        "build/native/libgit2",
        "girokmoji/native",
        build_type,
        cc_cmd,
        &.{
            b.fmt("-DCMAKE_C_COMPILER_LAUNCHER={s}", .{cc_launcher}),
            b.fmt("-DCMAKE_C_LINKER_LAUNCHER={s}", .{cc_launcher}),
            "-DBUILD_SHARED_LIBS=ON",
            "-DBUILD_CLAR=OFF",
            "-DBUILD_TESTS=OFF",
            "-DBUILD_EXAMPLES=OFF",
            "-DUSE_SHA1=mbedTLS",
            "-DUSE_HTTPS=mbedTLS",
            "-DUSE_SSH=OFF",
            "-DLIBGIT2_FILENAME=girokmoji_native",
            "-DCMAKE_C_STANDARD=99",
            "-DCMAKE_C_STANDARD_REQUIRED=ON",
            "-DCMAKE_C_LINKER_DEPFILE_SUPPORTED=FALSE",
            "-DCMAKE_C_LINK_DEPENDS_USE_LINKER=FALSE",
            b.fmt("-DCMAKE_C_FLAGS=-I{s}", .{libgit2_shim}),
            b.fmt("-DMBEDTLS_ROOT_DIR={s}", .{deps_prefix}),
            b.fmt("-DMBEDTLS_INCLUDE_DIR={s}/include", .{deps_prefix}),
            b.fmt("-DMBEDTLS_LIBRARY={s}/lib/libmbedtls.a", .{deps_prefix}),
            b.fmt("-DMBEDX509_LIBRARY={s}/lib/libmbedx509.a", .{deps_prefix}),
            b.fmt("-DMBEDCRYPTO_LIBRARY={s}/lib/libmbedcrypto.a", .{deps_prefix}),
            b.fmt("-DZLIB_ROOT={s}", .{deps_prefix}),
        },
    );
    libgit2.configure.step.dependOn(&mbedtls.install.step);
    libgit2.configure.step.dependOn(&zlib.install.step);

    const native = b.step("native", "Build libgit2 with mbedtls + zlib into girokmoji/native/lib");
    native.dependOn(&libgit2.install.step);

    b.default_step.dependOn(native);
}
