// sys-botbase-lab: a candidate set that lives on the Switch.
//
// The one-shot `search` command has to send every hit back over the network,
// which does not work when a common value matches hundreds of thousands of
// addresses. These commands keep the candidate list in the sysmodule instead.
// The PC starts a search, narrows it by re-reading only the stored addresses,
// and downloads the list once it is small enough to be useful.
//
//   searchNew <width> <value> <start> <size> [<start> <size> ...]
//   searchNext <op> [value]     ops: eq ne gt lt inc dec same diff
//   searchList <offset> <limit>
//   searchCount
//   searchReset
//
// searchNew, searchNext and searchCount all reply with the same status line:
//   <count> <width> <capped> <incomplete>

#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "commands.h"

#define SEARCH_CHUNK (512 * 1024)

// 150000 candidates at 16 bytes each is 2.4 MB. The sysmodule heap is 4.7 MB
// and the chunk buffer takes another 0.5 MB, so this fits without raising
// HEAP_SIZE. Raising it risks the console failing to boot, which would need a
// card reader to recover.
#define SEARCH_MAX_CANDIDATES 150000

typedef struct {
    u64 addr;
    u64 val;
} Candidate;

static Candidate* g_cands = NULL;
static u64 g_count = 0;
static u64 g_width = 4;
static bool g_capped = false;
static bool g_incomplete = false;

static u64 loadValue(const u8* p, u64 width)
{
    switch (width)
    {
        case 1: return *p;
        case 2: return *(const u16*)p;
        case 4: return *(const u32*)p;
        default: return *(const u64*)p;
    }
}

static bool validWidth(u64 width)
{
    return width == 1 || width == 2 || width == 4 || width == 8;
}

void searchReset(void)
{
    free(g_cands);
    g_cands = NULL;
    g_count = 0;
    g_capped = false;
    g_incomplete = false;
}

void searchCount(void)
{
    printf("%lu %lu %d %d\n", g_count, g_width, g_capped ? 1 : 0, g_incomplete ? 1 : 0);
}

void searchNew(u64 width, u64 value, u64* starts, u64* sizes, u64 count)
{
    if (!validWidth(width))
    {
        printf("ERR width\n");
        return;
    }
    searchReset();
    g_cands = malloc(sizeof(Candidate) * SEARCH_MAX_CANDIDATES);
    if (g_cands == NULL)
    {
        printf("ERR mem\n");
        return;
    }
    u8* buf = malloc(SEARCH_CHUNK);
    if (buf == NULL)
    {
        searchReset();
        printf("ERR mem\n");
        return;
    }
    g_width = width;

    attach();
    for (u64 r = 0; r < count && !g_capped; r++)
    {
        u64 addr = starts[r];
        u64 end = starts[r] + sizes[r];
        while (addr < end && !g_capped)
        {
            u64 n = end - addr;
            if (n > SEARCH_CHUNK)
                n = SEARCH_CHUNK;
            if (R_FAILED(readMem(buf, addr, n)))
            {
                g_incomplete = true;
                addr += n;
                continue;
            }
            for (u64 i = 0; i + width <= n; i += width)
            {
                if (loadValue(buf + i, width) == value)
                {
                    g_cands[g_count].addr = addr + i;
                    g_cands[g_count].val = value;
                    g_count++;
                    if (g_count >= SEARCH_MAX_CANDIDATES)
                    {
                        g_capped = true;
                        break;
                    }
                }
            }
            addr += n;
        }
    }
    detach();
    free(buf);
    searchCount();
}

// Re-read every stored candidate and keep the ones matching `op`. The stored
// value is updated to the value just read, so inc/dec/same/diff compare
// against the previous narrowing step rather than the original search.
void searchNext(const char* op, u64 value)
{
    if (g_cands == NULL)
    {
        printf("ERR nosearch\n");
        return;
    }
    u8 tmp[8];
    u64 keep = 0;

    attach();
    for (u64 i = 0; i < g_count; i++)
    {
        if (R_FAILED(readMem(tmp, g_cands[i].addr, g_width)))
        {
            g_incomplete = true;
            continue; // address no longer readable, drop it
        }
        u64 cur = loadValue(tmp, g_width);
        u64 prev = g_cands[i].val;
        bool ok;
        if (!strcmp(op, "eq"))        ok = (cur == value);
        else if (!strcmp(op, "ne"))   ok = (cur != value);
        else if (!strcmp(op, "gt"))   ok = (cur > value);
        else if (!strcmp(op, "lt"))   ok = (cur < value);
        else if (!strcmp(op, "inc"))  ok = (cur > prev);
        else if (!strcmp(op, "dec"))  ok = (cur < prev);
        else if (!strcmp(op, "same")) ok = (cur == prev);
        else if (!strcmp(op, "diff")) ok = (cur != prev);
        else
        {
            detach();
            printf("ERR op\n");
            return;
        }
        if (ok)
        {
            g_cands[keep].addr = g_cands[i].addr;
            g_cands[keep].val = cur;
            keep++;
        }
    }
    detach();

    g_count = keep;
    g_capped = false; // the set only shrinks from here
    searchCount();
}

// "<addr> <value> " pairs in hex, then a newline.
void searchList(u64 offset, u64 limit)
{
    if (g_cands == NULL)
    {
        printf("\n");
        return;
    }
    if (offset > g_count)
        offset = g_count;
    u64 end = offset + limit;
    if (end > g_count)
        end = g_count;
    for (u64 i = offset; i < end; i++)
        printf("%lX %lX ", g_cands[i].addr, g_cands[i].val);
    printf("\n");
}
