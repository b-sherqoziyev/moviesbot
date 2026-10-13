from aiogram.fsm.state import State, StatesGroup


class AdminChannelStates(StatesGroup):
    """Admin kanal qo'shish va boshqarish holatlari."""
    waiting_for_channel_id_or_forward = State()
    waiting_for_del_channel_id = State()


class AdminMovieStates(StatesGroup):
    """Admin film ko'rish va o'chirish holatlari."""
    waiting_for_info_code = State()
    waiting_for_del_code = State()
