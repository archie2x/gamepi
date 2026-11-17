#include <iostream>
#include <numeric>
#include <sys/utsname.h>
#include <unistd.h>
#include <vector>

int main()
{
    utsname system{};
    if (uname(&system) != 0)
        return 1;
    const std::vector<int> values{1, 2, 3, 4};
    std::cout << "Built on macOS with native Clang; running on "
              << system.sysname << ' ' << system.machine << '\n'
              << "Page size: " << sysconf(_SC_PAGESIZE) << '\n'
              << "C++ library check: "
              << std::accumulate(values.begin(), values.end(), 0) << '\n';
}
