from aiogram.fsm.state import State, StatesGroup

class AuthStates(StatesGroup):
    waiting_method = State()        # выбор метода
    waiting_phone = State()
    waiting_password = State()      # для входа по паролю
    waiting_code = State()          # для входа по SMS-коду
    waiting_captcha = State()