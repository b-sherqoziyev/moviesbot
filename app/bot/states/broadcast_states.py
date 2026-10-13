from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    """Xabar tarqatish (Broadcast) holatlari."""
    waiting_for_message = State()
    confirm_broadcast = State()
