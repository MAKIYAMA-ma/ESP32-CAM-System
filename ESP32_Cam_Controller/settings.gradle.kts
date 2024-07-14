pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
        maven { url = uri("https://jitpack.io" ) }
        // maven("https://jitpack.io") {
        //     content {
        //         includeGroupByRegex("com\\.github\\.hannesa2.*")
        //     }
        // }
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io" ) }
        maven { url = uri("https://niidp.pages.vcp-handson.org/sinetstream-android/") }
        maven { url = uri("https://repo.eclipse.org/content/repositories/paho-snapshots/") }
        // maven("https://jitpack.io") {
        //     content {
        //         includeGroupByRegex("com\\.github\\.hannesa2.*")
        //     }
        // }
    }
}

rootProject.name = "ESP32_Cam_Controller"
include(":app")
