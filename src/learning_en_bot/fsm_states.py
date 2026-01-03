"""
FSM States для управления состояниями бота
"""

from aiogram.fsm.state import State, StatesGroup


class ReminderStates(StatesGroup):
    """Состояния для управления напоминаниями"""
    waiting_for_morning_time = State()
    waiting_for_evening_time = State()
