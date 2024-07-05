#ifndef __COMMAND_RECIEVER_H
#define __COMMAND_RECIEVER_H

#include <queue>
#include <string>

class CommandFIFO {
public:
    CommandFIFO(size_t maxSize);

    void enqueue(const std::string& str);
    std::string dequeue();
    bool isEmpty() const;
    size_t size() const;

private:
    std::queue<std::string> fifo;
    size_t maxSize;
};

#endif  // __COMMAND_RECIEVER_H
