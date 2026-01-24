"""
FSM States для управления состояниями бота
"""

from aiogram.fsm.state import State, StatesGroup


class ReminderStates(StatesGroup):
    """Состояния для управления напоминаниями"""
    waiting_for_morning_time = State()
    waiting_for_evening_time = State()


class EditWordStates(StatesGroup):
    """Состояния для редактирования слов"""
    waiting_for_search_query = State()
    waiting_for_new_english = State()
    waiting_for_new_russian = State()
    waiting_for_new_transcription = State()
    waiting_for_new_topic = State()
