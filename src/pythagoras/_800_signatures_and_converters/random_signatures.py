import uuid

from .base_16_32_convertors import convert_int_to_base32

max_signature_length: int = 22

def get_random_signature() -> str:
    # random_int = uuid.uuid4().int + uuid.uuid1().int
    random_int = uuid.uuid4().int
    random_str = convert_int_to_base32(random_int)
    return random_str[:max_signature_length]
