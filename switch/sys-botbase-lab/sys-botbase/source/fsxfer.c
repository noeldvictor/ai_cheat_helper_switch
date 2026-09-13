// sys-botbase-lab: SD card file transfer over the existing command socket.
//
// The user accepted that sys-botbase is an unauthenticated LAN service and
// asked for this anyway, so their PC can push and pull files without an FTP
// app. The SD card is mounted only for the duration of one command because
// upstream removed fs use to avoid holding fs sessions.
//
// Paths are given without the "sdmc:" prefix, e.g. /switch/x.nro.

#include <switch.h>
#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

#include "commands.h"

#define FS_CHUNK (64 * 1024)

static bool fsBegin(void)
{
    if (R_FAILED(fsInitialize()))
        return false;
    if (R_FAILED(fsdevMountSdmc()))
    {
        fsExit();
        return false;
    }
    return true;
}

static void fsEnd(void)
{
    fsdevUnmountAll();
    fsExit();
}

static void fsPath(char* out, size_t outlen, const char* path)
{
    if (path[0] == '/')
        snprintf(out, outlen, "sdmc:%s", path);
    else
        snprintf(out, outlen, "sdmc:/%s", path);
}

// Lines of "<f|d>\t<size>\t<name>", then a final "END" line.
void fsList(const char* path)
{
    char full[512];
    fsPath(full, sizeof(full), path);
    if (!fsBegin())
    {
        printf("ERR mount\nEND\n");
        return;
    }
    DIR* d = opendir(full);
    if (d == NULL)
    {
        printf("ERR open %d\nEND\n", errno);
        fsEnd();
        return;
    }
    struct dirent* e;
    char child[1024];
    struct stat st;
    while ((e = readdir(d)) != NULL)
    {
        snprintf(child, sizeof(child), "%s/%s", full, e->d_name);
        u64 size = 0;
        char kind = 'f';
        if (stat(child, &st) == 0)
        {
            size = st.st_size;
            if (S_ISDIR(st.st_mode))
                kind = 'd';
        }
        printf("%c\t%lu\t%s\n", kind, size, e->d_name);
    }
    closedir(d);
    fsEnd();
    printf("END\n");
}

// Binary reply: 8-byte little-endian length (0 on failure), then the bytes.
void fsGet(const char* path)
{
    char full[512];
    fsPath(full, sizeof(full), path);
    u64 zero = 0;
    fflush(stdout);
    if (!fsBegin())
    {
        write(STDOUT_FILENO, &zero, sizeof(zero));
        return;
    }
    struct stat st;
    FILE* f = fopen(full, "rb");
    if (f == NULL || stat(full, &st) != 0)
    {
        if (f)
            fclose(f);
        fsEnd();
        write(STDOUT_FILENO, &zero, sizeof(zero));
        return;
    }
    u64 size = st.st_size;
    u8* buf = malloc(FS_CHUNK);
    if (buf == NULL)
    {
        fclose(f);
        fsEnd();
        write(STDOUT_FILENO, &zero, sizeof(zero));
        return;
    }
    write(STDOUT_FILENO, &size, sizeof(size));
    u64 sent = 0;
    while (sent < size)
    {
        size_t n = fread(buf, 1, FS_CHUNK, f);
        if (n == 0)
            break;
        size_t off = 0;
        while (off < n)
        {
            ssize_t w = write(STDOUT_FILENO, buf + off, n - off);
            if (w <= 0)
                break;
            off += w;
        }
        sent += n;
    }
    free(buf);
    fclose(f);
    fsEnd();
}

// Protocol: reply "OK", then read exactly `size` raw bytes from the socket,
// then reply "DONE <bytes>". A failure before the body replies "ERR ...".
void fsPut(const char* path, u64 size)
{
    char full[512];
    fsPath(full, sizeof(full), path);
    if (!fsBegin())
    {
        printf("ERR mount\n");
        return;
    }
    FILE* f = fopen(full, "wb");
    if (f == NULL)
    {
        printf("ERR open %d\n", errno);
        fsEnd();
        return;
    }
    u8* buf = malloc(FS_CHUNK);
    if (buf == NULL)
    {
        fclose(f);
        fsEnd();
        printf("ERR mem\n");
        return;
    }
    printf("OK\n");
    fflush(stdout);
    u64 got = 0;
    bool ok = true;
    while (got < size)
    {
        u64 want = size - got;
        if (want > FS_CHUNK)
            want = FS_CHUNK;
        ssize_t n = recv(STDOUT_FILENO, buf, want, 0);
        if (n <= 0)
        {
            ok = false;
            break;
        }
        if (fwrite(buf, 1, n, f) != (size_t)n)
        {
            ok = false;
            break;
        }
        got += n;
    }
    free(buf);
    fclose(f);
    fsEnd();
    if (ok)
        printf("DONE %lu\n", got);
    else
        printf("ERR short %lu\n", got);
}

void fsRename(const char* from, const char* to)
{
    char a[512], b[512];
    fsPath(a, sizeof(a), from);
    fsPath(b, sizeof(b), to);
    if (!fsBegin())
    {
        printf("ERR mount\n");
        return;
    }
    remove(b); // renaming over an existing file is not guaranteed on FAT
    int rc = rename(a, b);
    fsEnd();
    if (rc == 0)
        printf("OK\n");
    else
        printf("ERR %d\n", errno);
}

void fsDelete(const char* path)
{
    char full[512];
    fsPath(full, sizeof(full), path);
    if (!fsBegin())
    {
        printf("ERR mount\n");
        return;
    }
    int rc = remove(full);
    fsEnd();
    if (rc == 0)
        printf("OK\n");
    else
        printf("ERR %d\n", errno);
}

void fsMkdir(const char* path)
{
    char full[512];
    fsPath(full, sizeof(full), path);
    if (!fsBegin())
    {
        printf("ERR mount\n");
        return;
    }
    int rc = mkdir(full, 0777);
    fsEnd();
    if (rc == 0 || errno == EEXIST)
        printf("OK\n");
    else
        printf("ERR %d\n", errno);
}
