"""Câu truyền cảm hứng hiển thị ngẫu nhiên ở Tổng quan.

Tác giả là cách ghi phổ biến nhất; bạn có thể sửa hoặc thêm câu tại đây.
"""
import random

QUOTES = [
    {"text": "The only way to do great work is to love what you do.",
     "vi": "Cách duy nhất để làm nên việc lớn là yêu công việc mình đang làm.",
     "author": "Steve Jobs"},
    {"text": "It always seems impossible until it's done.",
     "vi": "Điều gì cũng có vẻ bất khả thi, cho đến khi nó được hoàn thành.",
     "author": "Nelson Mandela"},
    {"text": "The journey of a thousand miles begins with one step.",
     "vi": "Hành trình ngàn dặm bắt đầu từ một bước chân.",
     "author": "Lão Tử"},
    {"text": "Everything is difficult before it is easy.",
     "vi": "Mọi việc đều khó trước khi trở nên dễ dàng.",
     "author": "Saadi Shirazi"},
    {"text": "You miss 100% of the shots you don't take.",
     "vi": "Bạn bỏ lỡ 100% những cú sút mà bạn không thực hiện.",
     "author": "Wayne Gretzky"},
    {"text": "Alone we can do so little; together we can do so much.",
     "vi": "Một mình chúng ta làm được rất ít; cùng nhau, chúng ta làm được rất nhiều.",
     "author": "Helen Keller"},
    {"text": "Do one thing every day that scares you.",
     "vi": "Mỗi ngày hãy làm một việc khiến bạn thấy sợ.",
     "author": "Eleanor Roosevelt"},
    {"text": "What we think, we become.",
     "vi": "Điều chúng ta nghĩ, chúng ta sẽ trở thành.",
     "author": "Đức Phật"},
    {"text": "Education is the most powerful weapon which you can use to change the world.",
     "vi": "Giáo dục là vũ khí mạnh nhất để thay đổi thế giới.",
     "author": "Nelson Mandela"},
    {"text": "Knowing is not enough; we must apply. Willing is not enough; we must do.",
     "vi": "Biết thôi chưa đủ, phải áp dụng. Muốn thôi chưa đủ, phải hành động.",
     "author": "Johann Wolfgang von Goethe"},
]


def random_quote(exclude_index: int | None = None) -> tuple[int, dict]:
    """Chọn ngẫu nhiên một câu, tránh lặp lại câu vừa hiển thị."""
    choices = [i for i in range(len(QUOTES)) if i != exclude_index] or list(range(len(QUOTES)))
    index = random.choice(choices)
    return index, QUOTES[index]
