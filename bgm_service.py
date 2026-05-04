from collections import Counter

BUFFER_SIZE = 3
THRESHOLD = 0.7

def update_buffer(buffer, mood):
    buffer.append(mood)
    if len(buffer) > BUFFER_SIZE:
        buffer.pop(0)
    return buffer

def should_change_bgm(buffer):
    if len(buffer) < BUFFER_SIZE:
        return False, None

    counter = Counter(buffer)
    mood, count = counter.most_common(1)[0]

    if count / BUFFER_SIZE >= THRESHOLD:
        return True, mood

    return False, None