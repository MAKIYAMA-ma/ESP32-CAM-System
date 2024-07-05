#include "command_receiver.h"
#include <iostream>

CommandFIFO::CommandFIFO(size_t maxSize) : maxSize(maxSize) {}

void CommandFIFO::enqueue(const std::string& str) {
    if (str.length() > 16) {
        std::cerr << "Error: std::string length exceeds 16 characters" << std::endl;
        return;
    }
    if (fifo.size() == maxSize) {
        fifo.pop();
    }
    fifo.push(str);
}

std::string CommandFIFO::dequeue() {
    if (fifo.empty()) {
        return "";
    }
    std::string front = fifo.front();
    fifo.pop();
    return front;
}

bool CommandFIFO::isEmpty() const {
    return fifo.empty();
}

size_t CommandFIFO::size() const {
    return fifo.size();
}
