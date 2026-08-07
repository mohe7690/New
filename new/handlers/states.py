from aiogram.fsm.state import State, StatesGroup


class GroupFlow(StatesGroup):
    """Collecting front/back photos of one or more IDs to group onto an A4 sheet."""
    waiting_front = State()
    waiting_back = State()
    collecting_more = State()  # bulk mode: waiting for next front or 'Done'


class SmartImportFlow(StatesGroup):
    waiting_file = State()


class PaymentFlow(StatesGroup):
    awaiting_proof = State()


class AdminFlow(StatesGroup):
    awaiting_broadcast = State()
    awaiting_lookup_id = State()


class GenerateIDFlow(StatesGroup):
    """Collecting the data fields needed to render a new ID card from
    templates/front_blank.png + back_blank.png (processor.render_id_side)."""
    waiting_portrait = State()
    waiting_name_amh = State()
    waiting_name_eng = State()
    waiting_fan = State()
    waiting_fin = State()
    waiting_phone = State()
    waiting_address = State()
