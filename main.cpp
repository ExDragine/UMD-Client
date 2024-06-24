//  __  __     __    __     _____
// /\ \/\ \   /\ "-./  \   /\  __-.
// \ \ \_\ \  \ \ \-./\ \  \ \ \/\ \
//  \ \_____\  \ \_\ \ \_\  \ \____-
//   \/_____/   \/_/  \/_/   \/____/

#include <iostream>
#include <deque>
#include <vector>
#include <ctime>
#include <chrono>
#include <thread>
#include <string>
#include <fstream>
#include <iomanip>
#include <nlohmann/json.hpp> // for JSON handling
#include <curl/curl.h> // for HTTP requests
#include <serial/serial.h> // for serial communication
#include <filesystem>
#include <csignal>

using json = nlohmann::json;
namespace fs = std::filesystem;

// Load environment variables
std::string get_env_var(const std::string &key) {
    const char *val = getenv(key.c_str());
    return val == nullptr ? std::string("") : std::string(val);
}

std::string name = get_env_var("station_name");
std::string key = get_env_var("station_key");
std::string server = get_env_var("server");
int record_frequency = std::stoi(get_env_var("record_frequency"));
int storage_size = std::stoi(get_env_var("storage_size"));

std::string path = get_env_var("data_path").empty() ? fs::current_path().string() + "/data" : get_env_var("data_path");

// SN3003FSXCSN01 Class Definition
class SN3003FSXCSN01 {
public:
    SN3003FSXCSN01() {
        code = {
            {"wind_speed", {0x01, 0x03, 0x01, 0xF4, 0x00, 0x01, 0xC4, 0x04}},
            {"wind_scale", {0x01, 0x03, 0x01, 0xF5, 0x00, 0x01, 0x95, 0xC4}},
            {"wind_direction", {0x01, 0x03, 0x01, 0xF6, 0x00, 0x01, 0x65, 0xC4}},
            {"wind_angle", {0x01, 0x03, 0x01, 0xF7, 0x00, 0x01, 0x34, 0x04}},
            {"T&h", {0x01, 0x03, 0x01, 0xF8, 0x00, 0x02, 0x44, 0x06}},
            {"noise", {0x01, 0x03, 0x01, 0xFA, 0x00, 0x01, 0xA5, 0xC7}},
            {"pm2dot5", {0x01, 0x03, 0x01, 0xFB, 0x00, 0x01, 0xF4, 0x07}},
            {"pm10", {0x01, 0x03, 0x01, 0xFC, 0x00, 0x01, 0x45, 0xC6}},
            {"pressure", {0x01, 0x03, 0x01, 0xFD, 0x00, 0x01, 0x14, 0x06}},
            {"rain", {0x01, 0x03, 0x01, 0x01, 0x00, 0x01, 0xD4, 0x36}}
        };
        port.setPort("/dev/ttyS0");
        port.setBaudrate(4800);
        serial::Timeout to = serial::Timeout::simpleTimeout(100);
        port.setTimeout(to);
        port.open();
    }

    float get_data(const std::string &func) {
        port.write(code[func]);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        std::string response = port.read(7);
        if (response.size() == 7) {
            int data = (response[3] << 8) | response[4];
            if (func == "noise" || func == "rain") {
                return data / 10.0;
            } else if (func == "wind_speed" || func == "compass") {
                return data / 100.0;
            } else {
                return static_cast<float>(data);
            }
        } else {
            return 0.0;
        }
    }

    std::pair<float, float> get_th() {
        port.write(code["T&h"]);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        std::string response = port.read(9);
        if (response.size() == 9) {
            float h = ((response[3] << 8) | response[4]) / 10.0;
            float t = ((response[5] << 8) | response[6]) / 10.0;
            return {t, h};
        } else {
            return {0.0, 0.0};
        }
    }

private:
    serial::Serial port;
    std::map<std::string, std::vector<uint8_t>> code;
};

// DataTransfer Class Definition
class DataTransfer {
public:
    DataTransfer(const std::string &key, const std::string &name) : station_key(key), station_name(name) {
        if (station_key.empty() || station_name.empty()) {
            throw std::runtime_error("Station key or name is incorrect");
        }
    }

    void send_data(const std::string &server, const std::vector<std::string> &value_name, const std::string &filepath) {
        json p;
        p["id"] = station_name;
        p["timestamp"] = std::time(0);
        p["key"] = station_key;
        p["data"] = json::object();

        std::ifstream infile(filepath);
        std::string line;
        std::getline(infile, line);
        std::getline(infile, line);
        std::vector<std::string> values = split(line, ',');

        for (size_t i = 0; i < value_name.size(); ++i) {
            p["data"][value_name[i]] = std::stof(values[i]);
        }

        p["data"]["hold1"] = 0.0;
        p["data"]["hold2"] = 0.0;
        p["data"]["hold3"] = 0.0;

        transmit_data = p.dump(4);

        for (int i = 0; i < 3; ++i) {
            try {
                CURL *curl;
                CURLcode res;

                curl = curl_easy_init();
                if (curl) {
                    curl_easy_setopt(curl, CURLOPT_URL, server.c_str());
                    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, transmit_data.c_str());
                    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);

                    res = curl_easy_perform(curl);
                    if (res == CURLE_OK) {
                        break;
                    } else {
                        std::cerr << "HTTP request failed: " << curl_easy_strerror(res) << std::endl;
                    }
                    curl_easy_cleanup(curl);
                }
            } catch (const std::exception &e) {
                std::cerr << "Exception: " << e.what() << std::endl;
            }
        }
    }

private:
    std::string station_key;
    std::string station_name;
    std::string transmit_data;

    std::vector<std::string> split(const std::string &s, char delimiter) {
        std::vector<std::string> tokens;
        std::string token;
        std::istringstream tokenStream(s);
        while (std::getline(tokenStream, token, delimiter)) {
            tokens.push_back(token);
        }
        return tokens;
    }
};

// SensorHub Class Definition
class SensorHub {
public:
    SensorHub() : sn3003() {
        mem_data = std::deque<std::vector<float>>(record_frequency, std::vector<float>(9, 0.0));
        names = {"time", "temperature", "humidity", "wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"};
    }

    void update_mem() {
        std::vector<float> sensor_data(9, 0.0);
        sensor_data[0] = std::time(0);
        auto [t, h] = sn3003.get_th();
        sensor_data[1] = t;
        sensor_data[2] = h;

        std::this_thread::sleep_for(std::chrono::milliseconds(10));

        for (size_t i = 3; i < 9; ++i) {
            sensor_data[i] = sn3003.get_data(names[i]);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }

        mem_data.push_back(sensor_data);
        if (mem_data.size() > record_frequency) {
            mem_data.pop_front();
        }
    }

    void local_storage() {
        auto now = std::chrono::system_clock::now();
        std::time_t timestamp = std::chrono::system_clock::to_time_t(now);
        tm *ltm = std::localtime(&timestamp);
        std::string year = std::to_string(1900 + ltm->tm_year);
        std::string month = std::to_string(1 + ltm->tm_mon);
        std::string day = std::to_string(ltm->tm_mday);

        std::string everyday = path + "/" + year + "/" + month + "/" + day + ".csv";
        std::string latest_mean = path + "/latest_mean.csv";

        fs::create_directories(path + "/" + year + "/" + month);

        if (!fs::exists(everyday)) {
            std::ofstream outfile(everyday);
            outfile << join(names, ",") << std::endl;
        }

        if (!fs::exists(latest_mean)) {
            std::ofstream outfile(latest_mean);
            outfile << join(names, ",") << std::endl;
        }

        std::vector<float> mean_result(9, 0.0);
        for (size_t i = 1; i < 8; ++i) {
            float sum = 0.0;
            for (const auto &data : mem_data) {
                sum += data[i];
            }
            mean_result[i] = sum / mem_data.size();
        }
        mean_result[8] = mem_data.back()[8] - mem_data.front()[8];
        mean_result[0] = std::time(0);

        std::vector<std::vector<float>> mem_data_vector(mem_data.begin(), mem_data.end());
        append_to_file(everyday, mem_data_vector);
        append_to_file(latest_mean, mean_result, storage_size);

        DataTransfer transfer(key, name);
        transfer.send_data(server, names, latest_mean);
    }

private:
    SN3003FSXCSN01 sn3003;
    std::deque<std::vector<float>> mem_data;
    std::vector<std::string> names;

    template<typename T>
    std::string join(const std::vector<T> &vec, const std::string &delim) {
        std::ostringstream result;
        for (size_t i = 0; i < vec.size(); ++i) {
            result << vec[i];
            if (i < vec.size() - 1) {
                result << delim;
            }
        }
        return result.str();
    }

    void append_to_file(const std::string &filepath, const std::vector<std::vector<float>> &data) {
        std::ofstream outfile(filepath, std::ios::app);
        for (const auto &row : data) {
            outfile << join(row, ",") << std::endl;
        }
    }

    void append_to_file(const std::string &filepath, const std::vector<float> &data, size_t max_size) {
        std::ifstream infile(filepath);
        std::vector<std::string> lines((std::istream_iterator<std::string>(infile)), std::istream_iterator<std::string>());
        infile.close();

        if (lines.size() > max_size + 1) {
            lines.erase(lines.begin() + 1, lines.begin() + lines.size() - max_size);
        }

        std::ofstream outfile(filepath);
        for (const auto &line : lines) {
            outfile << line << std::endl;
        }
        outfile << join(data, ",") << std::endl;
    }
};



// Signal handler for graceful shutdown
void signal_handler(int signal) {
    std::cout << "Signal received, exiting..." << std::endl;
    std::exit(0);
}

int main() {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    SensorHub sensor_probe;
    while (true) {
        sensor_probe.update_mem();
        sensor_probe.local_storage();
        std::this_thread::sleep_for(std::chrono::seconds(record_frequency));
    }
    return 0;
}
