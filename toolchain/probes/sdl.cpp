#include <SDL.h>
#include <iostream>

int main()
{
    SDL_version runtime{};
    SDL_GetVersion(&runtime);
    std::cout << "SDL headers: " << SDL_MAJOR_VERSION << '.' << SDL_MINOR_VERSION
              << '.' << SDL_PATCHLEVEL << "\nSDL runtime: "
              << int(runtime.major) << '.' << int(runtime.minor) << '.'
              << int(runtime.patch) << "\nVideo backends:";
    bool kms = false;
    for (int i = 0; i < SDL_GetNumVideoDrivers(); ++i) {
        const char* driver = SDL_GetVideoDriver(i);
        std::cout << ' ' << driver;
        kms |= SDL_strcmp(driver, "KMSDRM") == 0;
    }
    std::cout << '\n';
    if (SDL_Init(SDL_INIT_GAMECONTROLLER) != 0) {
        std::cerr << SDL_GetError() << '\n';
        return 1;
    }
    std::cout << "Controller initialization succeeded; joysticks: "
              << SDL_NumJoysticks() << '\n';
    SDL_Quit();
    return kms ? 0 : 2;
}
