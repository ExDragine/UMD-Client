#include <iostream>
#include <fstream>
#include <deque>
#include <vector>
#include <string>
#include <ctime>
#include <chrono>
#include <thread>
#include <iomanip>
#include <libserialport.h>
#include <json/json.h>
#include <curl/curl.h>
#include <filesystem> // 添加这个头文件

namespace fs = std::filesystem; // 使用std::filesystem

// Configuration variables
std::string name = "your_station_name";
std::string key = "your_station_key";
std::string server = "your_server_url";
int record_frequency = 30;
int storage_size = 2880;
std::string path = "./data";

// Serial port setup
struct sp_port *port;

void initialize_serial() {
    sp_get_port_by_name("/dev/ttyS0", &port);
    sp_open(port, SP_MODE_READ_WRITE);
    sp_set_baudrate(port, 4800);
    sp_set_bits(port, 8);
    sp_set_parity(port, SP_PARITY_NONE);
    sp_set_stopbits(port, 1);
    sp_set_flowcontrol(port, SP_FLOWCONTROL_NONE);
}

class SN3003FSXCSN01 {
public:
    std::map<std::string, std::vector<uint8_t>> code = {
        {"wind_speed", {0x01, 0x03, 0x01, 0xF4, 0x00, 0x01, 0xC4, 0x04}},
        {"wind_scale", {0x01, 0x03, 0x01, 0xF5, 0x00, 0x01, 0x95, 0xC4}},
        {"wind_direction", {0x01, 0x03, 0x01, 0xF6, 0x00, 0x01, 0x65, 0xC4}},
        {"wind_angle", {0x01, 0x03, 0x01, 0xF7, 0x00, 0x01, 0x34, 0x04}},
        {"T&h", {0x01, 0x03, 0x01, 0xF8, 0x00, 0x02, 0x44, 0x06}},
        {"noise", {0x01, 0x03, 0x01, 0xFA, 0x00, 0x01, 0xA5, 0xC7}},
        {"pm2dot5", {0x01, 0x03, 0x01, 0xFB, 0x00, 0x01, 0xF4, 0x07}},
        {"pm10", {0x01, 0x03, 0x01, 0xFC, 0x00, 0x01, 0x45, 0xC6}},
        {"pressure", {0x01, 0x03, 0x01, 0xFD, 0x00, 0x01, 0x14, 0x06}},
        {"rain", {0x01, 0x03, 0x01, 0x01, 0x00, 0x01, 0xD4, 0x36}},
    };

    float get_data(const std::string& func) {
        sp_blocking_write(port, code[func].data(), code[func].size(), 100);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        uint8_t response[7];
        int bytes_read = sp_blocking_read(port, response, 7, 100);
        if (bytes_read == 7) {
            int data = (response[3] << 8) | response[4];
            if (func == "noise" || func == "rain") {
                return static_cast<float>(data) / 10.0;
            } else if (func == "wind_speed") {
                return static_cast<float>(data) / 100.0;
            } else {
                return static_cast<float>(data);
            }
        }
        return 0.0;
    }

    std::pair<float, float> get_th() {
        sp_blocking_write(port, code["T&h"].data(), code["T&h"].size(), 100);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        uint8_t response[9];
        int bytes_read = sp_blocking_read(port, response, 9, 100);
        if (bytes_read == 9) {
            float h = static_cast<float>((response[3] << 8) | response[4]) / 10.0;
            float t = static_cast<float>((response[5] << 8) | response[6]) / 10.0;
            return {t, h};
        }
        return {0.0, 0.0};
    }
};

class DataTransfer {
public:
    DataTransfer(const std::string& key, const std::string& name) : station_key(key), station_name(name) {
        initial_check();
    }

    std::string transform_data(const std::vector<std::string>& value_name, const std::vector<float>& value) {
        Json::Value data;
        for (size_t i = 0; i < value_name.size(); ++i) {
            data[value_name[i]] = value[i];
        }
        data["hold1"] = 0.0;
        data["hold2"] = 0.0;
        data["hold3"] = 0.0;

        Json::Value root;
        root["id"] = station_name;
        root["timestamp"] = static_cast<int>(std::time(nullptr));
        root["key"] = station_key;
        root["data"] = data;

        Json::StreamWriterBuilder writer;
        std::string output = Json::writeString(writer, root);
        return output;
    }

    void send_data(const std::string& server, const std::vector<std::string>& value_name, const std::vector<float>& value) {
        std::string data = transform_data(value_name, value);
        for (int i = 0; i < 3; ++i) {
            CURL* curl = curl_easy_init();
            if (curl) {
                CURLcode res;
                curl_easy_setopt(curl, CURLOPT_URL, server.c_str());
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
                res = curl_easy_perform(curl);
                if (res == CURLE_OK) {
                    long http_code = 0;
                    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
                    if (http_code == 200 || http_code == 201) {
                        break;
                    } else if (http_code == 202) {
                        std::this_thread::sleep_for(std::chrono::seconds(5));
                        break;
                    }
                }
                curl_easy_cleanup(curl);
            }
        }
    }

private:
    std::string station_key;
    std::string station_name;

    void initial_check() {
        if (station_key.empty() || station_name.empty()) {
            throw std::invalid_argument("Key or station name is incorrect.");
        }
    }
};

class SensorHub {
public:
    SensorHub() : sn3003() {
        mem_data.resize(record_frequency, std::vector<float>(funcs.size() + 3, 0.0));
    }

    void update_mem() {
        std::vector<float> sensor_data(funcs.size() + 3, 0.0);
        sensor_data[0] = static_cast<float>(std::time(nullptr));
        auto [t, h] = sn3003.get_th();
        sensor_data[1] = t;
        sensor_data[2] = h;

        for (size_t i = 0; i < funcs.size(); ++i) {
            sensor_data[i + 3] = sn3003.get_data(funcs[i]);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }

        mem_data.pop_front();
        mem_data.push_back(sensor_data);
    }

    void local_storage() {
        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        std::tm buf;
        localtime_r(&in_time_t, &buf);
        std::ostringstream oss;
        oss << std::put_time(&buf, "%Y/%m/%d");
        std::string date_path = oss.str();

        fs::create_directories(path + "/" + date_path);

        std::ofstream everyday(path + "/" + date_path + ".csv", std::ios_base::app);
        std::ofstream latest_mean(path + "/latest_mean.csv", std::ios_base::app);

        if (mem_data.size() > 1) {
            std::vector<float> mean_result(funcs.size() + 3, 0.0);
            mean_result[0] = static_cast<float>(std::time(nullptr));

            for (size_t i = 1; i < mem_data.size() - 1; ++i) {
                for (size_t j = 1; j < mean_result.size(); ++j) {
                    mean_result[j] += mem_data[i][j];
                }
            }
            for (size_t j = 1; j < mean_result.size(); ++j) {
                mean_result[j] /= static_cast<float>(mem_data.size() - 1);
            }
            mean_result.back() = mem_data.back().back() - mem_data.front().back();

            everyday << join(mem_data.back()) << "\n";
            latest_mean << join(mean_result) << "\n";
        }

        DataTransfer transfer(key, name);
        transfer.send_data(server, names, mem_data.back());
    }

private:
    SN3003FSXCSN01 sn3003;
    std::deque<std::vector<float>> mem_data;
    std::vector<std::string> names = {"time", "temperature", "humidity", "wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"};
    std::vector<std::string> funcs = {"wind_speed", "wind_angle", "noise", "pm2dot5", "pm10", "pressure", "rain"};

    std::string join(const std::vector<float>& data) {
        std::ostringstream oss;
        for (size_t i = 0; i < data.size(); ++i) {
            if (i != 0) {
                oss << ",";
            }
            oss << data[i];
        }
        return oss.str();
    }
};

int main() {
    initialize_serial();

    SensorHub sensor_pobe;
    std::thread update_thread([&]() {
        while (true) {
            sensor_pobe.update_mem();
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    });

    std::thread storage_thread([&]() {
        while (true) {
            sensor_pobe.local_storage();
            std::this_thread::sleep_for(std::chrono::seconds(record_frequency));
        }
    });

    update_thread.join();
    storage_thread.join();

    sp_close(port);
    sp_free_port(port);

    return 0;
}
