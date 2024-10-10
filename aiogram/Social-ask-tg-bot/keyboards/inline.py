from aiogram.utils.keyboard import InlineKeyboardBuilder

# Admin main Menu
main_menu_builder = InlineKeyboardBuilder()
main_menu_builder.button(text="Адміністратор", callback_data="admin")
main_menu_builder.button(text="Опитування", callback_data="poll")
main_menu_builder.button(text="Перегляд результатів", callback_data="results")
main_menu_builder.button(text="Додати нагороду", callback_data="reward")
main_menu_builder.adjust(2)

# Admin menu
admin_builder = InlineKeyboardBuilder()
admin_builder.button(text="Додати адміністратора", callback_data="add_admin")
admin_builder.button(text="Показати адмінiстраторiв", callback_data="show_admin")
admin_builder.button(text="Змінити ім'я адміністратора", callback_data="edit_admin")
admin_builder.button(text="Видалити адміністратора", callback_data="delete_admin")
admin_builder.button(text="Назад", callback_data="go_back_to_start")
admin_builder.adjust(2, 2, 1)

# Add poll menu
poll_builder = InlineKeyboardBuilder()
poll_builder.button(text="Створити опитування", callback_data="create_poll")
poll_builder.button(text="Змінити опитування", callback_data="edit_poll")
poll_builder.button(text="Назад", callback_data="go_back_to_start")
poll_builder.adjust(2, 1)

# Show description to user
show_desc_builder = InlineKeyboardBuilder()
show_desc_builder.button(text="Окей!", callback_data="start_poll")
show_desc_builder.button(text="Назад", callback_data="go_back_to_start_user")
