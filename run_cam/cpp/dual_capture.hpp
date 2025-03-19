#include <iostream>
#include <thread>
#include <atomic>
#include <chrono>
#include <string>
#include <vector>
#include <memory>
#include <fstream>
#include <filesystem>

// libcamera headers
#include <libcamera/camera_manager.h>
#include <libcamera/camera.h>
#include <libcamera/camera_configuration.h>
#include <libcamera/stream.h>
#include <libcamera/framebuffer.h>
#include <libcamera/framebuffer_allocator.h>
#include <libcamera/request.h>

// For image encoding, you might need something like libjpeg or OpenCV
// to convert raw buffers to JPG. This example uses a stub "writeDummyImage()" function.

namespace fs = std::filesystem;

// Global stop flag
std::atomic<bool> g_stop(false);

struct MyCamera {
    std::shared_ptr<libcamera::Camera> camera;
    std::unique_ptr<libcamera::CameraConfiguration> config;
    std::unique_ptr<libcamera::FrameBufferAllocator> allocator;
    libcamera::Stream *stream;
    // Additional fields if needed
};

// ----------------------------------------------------------------------------
// A placeholder function that “writes an image” for demonstration.
// In a real scenario, you’d convert the raw buffer to JPEG or something else.
// ----------------------------------------------------------------------------
void writeDummyImage(const std::string &filename, int width, int height, int frameIndex)
{
    // Just create a blank text file to represent the "image".
    // Replace with real code to convert the libcamera buffer into a .jpg or .png.
    std::ofstream ofs(filename);
    ofs << "Dummy image: " << width << "x" << height << " frame # " << frameIndex << "\n";
    ofs.close();
}

// ----------------------------------------------------------------------------
// Captures N frames from camera0 in a separate thread, saving to fdir_cam0
// ----------------------------------------------------------------------------
void captureCamera0(MyCamera &cam0, int numFrames, const std::string &fdir_cam0)
{
    // Start capturing
    int ret = cam0.camera->start();
    if (ret) {
        std::cerr << "[cam0] Failed to start camera.\n";
        return;
    }

    std::cout << "[cam0] Started capturing. Will capture " << numFrames << " frames.\n";

    // For a real pipeline, you'd queue Requests, wait for them, process buffers, etc.
    // This example just simulates capturing:
    for (int i = 0; i < numFrames && !g_stop; i++) {
        // Simulate actual capture time:
        std::this_thread::sleep_for(std::chrono::milliseconds(50));

        // Here you'd wait for Request completion. We'll pretend we have a buffer:
        std::string outName = fdir_cam0 + "0_frame_" + std::to_string(i) + ".jpg";
        // “Write” a dummy image
        writeDummyImage(outName, cam0.config->at(0).size.width, cam0.config->at(0).size.height, i);
        std::cout << "[cam0] Wrote " << outName << "\n";
    }

    cam0.camera->stop();
    std::cout << "[cam0] Capture thread finished.\n";
}

// ----------------------------------------------------------------------------
// Captures N frames from camera1 in a separate thread, saving to fdir_cam1
// ----------------------------------------------------------------------------
void captureCamera1(MyCamera &cam1, int numFrames, const std::string &fdir_cam1)
{
    int ret = cam1.camera->start();
    if (ret) {
        std::cerr << "[cam1] Failed to start camera.\n";
        return;
    }

    std::cout << "[cam1] Started capturing. Will capture " << numFrames << " frames.\n";

    for (int i = 0; i < numFrames && !g_stop; i++) {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));

        std::string outName = fdir_cam1 + "1_frame_" + std::to_string(i) + ".jpg";
        writeDummyImage(outName, cam1.config->at(0).size.width, cam1.config->at(0).size.height, i);
        std::cout << "[cam1] Wrote " << outName << "\n";
    }

    cam1.camera->stop();
    std::cout << "[cam1] Capture thread finished.\n";
}

// ----------------------------------------------------------------------------
// Configure a camera with a simple "still capture" config
// For real usage, you’d set exposure, pixel format, etc.
// ----------------------------------------------------------------------------
bool configureCamera(MyCamera &mycam, int width, int height)
{
    if (!mycam.camera) {
        std::cerr << "Camera not found!\n";
        return false;
    }
    if (mycam.camera->acquire()) {
        std::cerr << "Failed to acquire camera!\n";
        return false;
    }

    libcamera::StreamRoles streamRoles{ libcamera::StreamRole::StillCapture };
    auto config = mycam.camera->generateConfiguration(streamRoles);
    if (!config || config->size() == 0) {
        std::cerr << "Failed to generate configuration.\n";
        mycam.camera->release();
        return false;
    }

    auto &cfg = config->at(0);
    cfg.size.width = width;
    cfg.size.height = height;
    // Pixel format, bufferCount, etc. can be set here if needed:
    // cfg.pixelFormat = libcamera::formats::BGR888; // example

    config->validate();
    if (mycam.camera->configure(config.get())) {
        std::cerr << "Failed to configure camera.\n";
        mycam.camera->release();
        return false;
    }

    mycam.config = std::move(config);
    mycam.stream = mycam.config->at(0).stream();

    // Allocate buffers
    mycam.allocator = std::make_unique<libcamera::FrameBufferAllocator>(mycam.camera);
    int res = mycam.allocator->allocate(mycam.stream);
    if (res < 0) {
        std::cerr << "Failed to allocate buffers.\n";
        mycam.camera->release();
        return false;
    }

    // Let’s not queue requests in this example, we’ll do a simplified approach
    return true;
}

// ----------------------------------------------------------------------------
// main(): parse arguments, set up cameras, spawn threads, wait, then exit
// ----------------------------------------------------------------------------
int main(int argc, char *argv[])
{
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <num_frames> <dir_cam0> <dir_cam1>\n";
        return 1;
    }

    int numFrames = std::stoi(argv[1]);
    std::string fdir_cam0 = argv[2];
    std::string fdir_cam1 = argv[3];

    // Ensure directories exist
    fs::create_directories(fdir_cam0);
    fs::create_directories(fdir_cam1);

    // Start libcamera's CameraManager
    libcamera::CameraManager camMan;
    int ret = camMan.start();
    if (ret) {
        std::cerr << "Failed to start CameraManager.\n";
        return 1;
    }

    auto cameras = camMan.cameras();
    if (cameras.size() < 2) {
        std::cerr << "Not enough cameras found. Need at least 2.\n";
        return 1;
    }

    // Assign to our global MyCamera structs
    MyCamera cam0, cam1;
    cam0.camera = cameras[0];
    cam1.camera = cameras[1];

    // In real usage, you might pick a mode from arguments, e.g. 1440x1080
    // or pass it in from Python. Hardcode for demonstration:
    if (!configureCamera(cam0, 1440, 1080)) {
        std::cerr << "Failed to configure cam0.\n";
        return 1;
    }
    if (!configureCamera(cam1, 1440, 1080)) {
        std::cerr << "Failed to configure cam1.\n";
        return 1;
    }

    std::cout << "Launching capture threads for " << numFrames << " frames.\n";

    // Launch threads
    std::thread t0(captureCamera0, std::ref(cam0), numFrames, fdir_cam0);
    std::thread t1(captureCamera1, std::ref(cam1), numFrames, fdir_cam1);

    // Wait for them to finish
    t0.join();
    t1.join();

    // Release cameras
    cam0.camera->release();
    cam1.camera->release();

    // Stop manager
    camMan.stop();

    std::cout << "Dual capture complete.\n";
    return 0;
}
