#include <cstdint>

struct alignas(16) vec_t {
  uint64_t a, b;
};

int main() {
  constexpr uint64_t gprs[] = {
    0x0001020304050607,
    0x1011121314151617,
    0x2021222324252627,
    0x3031323334353637,
    0x4041424344454647,
    0x5051525354555657,
    0x6061626364656667,
    0x7071727374757677,
  };

  constexpr vec_t vecs[] = {
    { 0x0F0E0D0C0B0A0908, 0x1716151413121110, },
    { 0x100F0E0D0C0B0A09, 0x1817161514131211, },
    { 0x11100F0E0D0C0B0A, 0x1918171615141312, },
    { 0x1211100F0E0D0C0B, 0x1A19181716151413, },
    { 0x131211100F0E0D0C, 0x1B1A191817161514, },
    { 0x14131211100F0E0D, 0x1C1B1A1918171615, },
    { 0x1514131211100F0E, 0x1D1C1B1A19181716, },
    { 0x161514131211100F, 0x1E1D1C1B1A191817, },
  };

  asm volatile(
    "ldp      x0,  x1,  [%0]\n\t"
    "ldp      x2,  x3,  [%0, #16]\n\t"
    "ldp      x4,  x5,  [%0, #32]\n\t"
    "ldp      x6,  x7,  [%0, #48]\n\t"
    "\n\t"
    "ld1      {v0.2d, v1.2d, v2.2d, v3.2d}, [%1], #64\n\t"
    "ld1      {v4.2d, v5.2d, v6.2d, v7.2d}, [%1], #64\n\t"
    "\n\t"
    "brk      #0\n\t"
    :
    : "r"(gprs), "r"(vecs)
    : "x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7",
      "v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7"
  );

  return 0;
}