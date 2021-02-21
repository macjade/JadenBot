import requests
import logging

from uuid import uuid4

import telegram

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQuery, InlineQueryResultArticle, KeyboardButton, \
    ReplyKeyboardMarkup, PollAnswer, InputTextMessageContent, ParseMode
from telegram.ext import Updater, InlineQueryHandler, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown

import os
PORT = int(os.environ.get('PORT', 5000))
TOKEN = str(os.environ.get('TEL_BOT_TOKEN'))

#Enabling Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

Industry = [
    ('/restaurant', 'food vendors'),
    ('/gadgets', 'gadget vendors'),
    ('/fashion', 'fashion vendors'),
]

def retvendors():
    industry = ""
    for i,j in Industry:
        industry += f'\n {i} - {j} '

    return industry

def start(bot, update):
    """Send a message when the command /start is issued."""

    bot.message.reply_sticker(sticker='http://thumbs.gfycat.com/BlindAstonishingAfricanelephant-size_restricted.gif')
    bot.message.reply_text(text="""
    Welcome to <b>Jaden</b> retail bot. \n\n I am here to help you with your ordering tasks. \n\n /help for more info
    """, parse_mode=ParseMode.HTML)
    bot.message.reply_text(text="Please wait while we are verifying your profile...")

    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': bot.message.chat_id})

    user = response.json().get('status')

    if user:
        bot.message.reply_text(text="Welcome Back "+response.json().get('name'))
        help(bot, update)
    else:
        keyboard = []
        keyboard.append([InlineKeyboardButton(u'Continue', callback_data='register_profile')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.message.reply_text(text="Sorry! your profile doesn't exists in our records. Tap <b>Continue</b> to register your profile.", parse_mode=ParseMode.HTML, reply_markup=reply_markup)

def sortbutton(bot, update):

    query = bot.callback_query
    data = query.data

    if data == 'register_profile':

        firstname = bot.callback_query.message.chat.first_name
        lastname = bot.callback_query.message.chat.last_name

        params = {
            'id': query.message.chat_id,
            'firstname': firstname,
            'lastname': lastname if lastname else '',
        }

        response = requests.post('http://127.0.0.1:8000/account/users/', data=params)
        user = response.json()

        if user.get('status'):
            query.message.reply_text(text="""<b>Your profile has been registered.</b> Complete the following process to complete your profile""" + u'\u270A', parse_mode=ParseMode.HTML)

            up_param = {
                'id': query.message.chat_id,
                'tag': 'prof_gender_new',
            }

            response = requests.post('http://127.0.0.1:8000/questiontag/question/', data=up_param)
            userprocess = response.json()

            if userprocess.get('status'):

                keyboard = [[KeyboardButton('Male'), KeyboardButton('Female'), KeyboardButton('Others')]]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                query.message.reply_text(text='Send me your gender to update your profile.', reply_markup=reply_markup)
            else:
                query.message.reply_text(text='Error updating your profile.')
        else:
            query.message.reply_text(text=user.get('message'), parse_mode=ParseMode.HTML)

    elif data == 'prof_gender':
        up_param = {
            'id': query.message.chat_id,
            'tag': 'prof_gender',
        }

        response = requests.post('http://127.0.0.1:8000/questiontag/question/', data=up_param)
        userprocess = response.json()
        if userprocess.get('status'):
            keyboard = [[KeyboardButton('Male'), KeyboardButton('Female'), KeyboardButton('Others')]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            query.message.reply_text(text='OK. Send me your new gender to update your profile.', reply_markup=reply_markup)

    elif data == 'prof_location':
        up_param = {
            'id': query.message.chat_id,
            'tag': 'prof_location',
        }

        response = requests.post('http://127.0.0.1:8000/questiontag/question/', data=up_param)
        userprocess = response.json()

        if userprocess.get('status'):
            keyboard = [[KeyboardButton('Abuja'), KeyboardButton('Enugu'), KeyboardButton('Ekiti'), KeyboardButton('Lagos'), KeyboardButton('Ogun'), KeyboardButton('Port Harcourt')]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            query.message.reply_text(text='OK. Send me your new location to update your profile.', reply_markup=reply_markup)

    elif data.startswith('add_cart'):

        itemid = str(data).replace('add_cart_', '')

        response = requests.get('http://127.0.0.1:8000/order/getitem/', params={'id': int(itemid)})
        item = response.json()

        response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': query.message.chat_id, 'tag': 'add_cart_' + itemid})
        resp_cart = response.json().get('status')

        if item['status'] and resp_cart :
            query.message.reply_text(text="""OK. How many <b>"""+str(item['name'])+"""</b> do you want to order?\n <b>Unit Price: </b>""" + f"{float(item['price']):,.2f}", parse_mode=ParseMode.HTML)
        else:
            query.message.reply_text(text="""Unable to process your request at the moment.""", parse_mode=ParseMode.HTML)

    elif data.startswith('restaurant_'):
        vendor_q = data.split('_')

        if len(vendor_q) == 2:
            response = requests.get('http://127.0.0.1:8000/products/menu', params={'id': int(vendor_q[1])})
            menu = response.json()

            if menu.get('status'):
                keyboard = []
                temp_key = []

                for men in menu['menu']:
                    if len(temp_key) == 2:
                        keyboard.append(temp_key)
                        temp_key = []
                    print(men[0], vendor_q[1], men[1])
                    temp_key.append(InlineKeyboardButton(u'' + str(men[0]).capitalize(), callback_data='restaurant_' + str(vendor_q[1]) + '_' + str(men[1])))

                if len(temp_key) != 0:
                    keyboard.append(temp_key)
                    temp_key = []

                reply_markup = InlineKeyboardMarkup(keyboard)
                update.bot.edit_message_text(
                    chat_id = query.message.chat_id,
                    message_id = query.message.message_id,
                    text="<b>"+str(menu['name'])+" Menu</b> \n\n Please select and item from the categroies to view products available for purchase",
                    parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            else:
                query.message.reply_text(
                    text=str(menu['message']),
                    parse_mode=ParseMode.HTML)

        if len(vendor_q) == 3:

            response = requests.get('http://127.0.0.1:8000/products/menuitem', params={'id': int(vendor_q[2])})
            item = response.json()

            if item.get('status'):

                for i in item['item']:
                    keyboard = []

                    keyboard.append([InlineKeyboardButton(u'Add to cart', callback_data='add_cart_' + str(i[1]))])

                    query.message.reply_photo(photo=str(i[4]))
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    query.message.reply_text(
                        text="<b>Name: </b>" + str(i[0]) + " \n<b>Description: </b>"+ str(i[2]) + " \n<b>Price: </b>"+ str(i[3]),
                        parse_mode=ParseMode.HTML, reply_markup=reply_markup)

            else:
                query.message.reply_text(
                    text=str(item['message']),
                    parse_mode=ParseMode.HTML)

    elif data.startswith('gadgets_'):
        vendor_q = data.split('_')

        if len(vendor_q) == 2:
            response = requests.get('http://127.0.0.1:8000/products/menu', params={'id': int(vendor_q[1])})
            menu = response.json()

            if menu.get('status'):
                keyboard = []
                temp_key = []

                for men in menu['menu']:
                    if len(temp_key) == 2:
                        keyboard.append(temp_key)
                        temp_key = []
                    print(men[0], vendor_q[1], men[1])
                    temp_key.append(InlineKeyboardButton(u'' + str(men[0]).capitalize(), callback_data='gadgets_' + str(vendor_q[1]) + '_' + str(men[1])))

                if len(temp_key) != 0:
                    keyboard.append(temp_key)
                    temp_key = []

                reply_markup = InlineKeyboardMarkup(keyboard)
                update.bot.edit_message_text(
                    chat_id = query.message.chat_id,
                    message_id = query.message.message_id,
                    text="<b>"+str(menu['name'])+" Menu</b> \n\n Please select and item from the categroies to view products available for purchase",
                    parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            else:
                query.message.reply_text(
                    text=str(menu['message']),
                    parse_mode=ParseMode.HTML)

        if len(vendor_q) == 3:

            response = requests.get('http://127.0.0.1:8000/products/menuitem', params={'id': int(vendor_q[2])})
            item = response.json()

            if item.get('status'):

                for i in item['item']:
                    keyboard = []

                    keyboard.append([InlineKeyboardButton(u'Add to cart', callback_data='add_cart_' + str(i[1]))])

                    query.message.reply_photo(photo=str(i[4]))
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    query.message.reply_text(
                        text="<b>Name: </b>" + str(i[0]) + " \n<b>Description: </b>"+ str(i[2]) + " \n<b>Price: </b>"+ str(i[3]),
                        parse_mode=ParseMode.HTML, reply_markup=reply_markup)

            else:
                query.message.reply_text(
                    text=str(item['message']),
                    parse_mode=ParseMode.HTML)

    elif data.startswith('fashion_'):
        vendor_q = data.split('_')

        if len(vendor_q) == 2:
            response = requests.get('http://127.0.0.1:8000/products/menu', params={'id': int(vendor_q[1])})
            menu = response.json()

            if menu.get('status'):
                keyboard = []
                temp_key = []

                for men in menu['menu']:
                    if len(temp_key) == 2:
                        keyboard.append(temp_key)
                        temp_key = []
                    print(men[0], vendor_q[1], men[1])
                    temp_key.append(InlineKeyboardButton(u'' + str(men[0]).capitalize(), callback_data='fashion_' + str(vendor_q[1]) + '_' + str(men[1])))

                if len(temp_key) != 0:
                    keyboard.append(temp_key)
                    temp_key = []

                reply_markup = InlineKeyboardMarkup(keyboard)
                update.bot.edit_message_text(
                    chat_id = query.message.chat_id,
                    message_id = query.message.message_id,
                    text="<b>"+str(menu['name'])+" Menu</b> \n\n Please select and item from the categroies to view products available for purchase",
                    parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            else:
                query.message.reply_text(
                    text=str(menu['message']),
                    parse_mode=ParseMode.HTML)

        if len(vendor_q) == 3:

            response = requests.get('http://127.0.0.1:8000/products/menuitem', params={'id': int(vendor_q[2])})
            item = response.json()

            if item.get('status'):

                for i in item['item']:
                    keyboard = []

                    keyboard.append([InlineKeyboardButton(u'Add to cart', callback_data='add_cart_' + str(i[1]))])

                    query.message.reply_photo(photo=str(i[4]))
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    query.message.reply_text(
                        text="<b>Name: </b>" + str(i[0]) + " \n<b>Description: </b>"+ str(i[2]) + " \n<b>Price: </b>"+ str(i[3]),
                        parse_mode=ParseMode.HTML, reply_markup=reply_markup)

            else:
                query.message.reply_text(
                    text=str(item['message']),
                    parse_mode=ParseMode.HTML)

    elif data == 'remove_all':
        response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': query.message.chat_id, 'tag': 'remove_cart'})
        qt_cart = response.json().get('status')

        if qt_cart:
            removeitem(query, update, 'all')

    elif data == 'checkout':
        checkoutitem(query, update)

def help(bot, update):
    """Send a message when the command /help is issued."""
    bot.message.reply_text(text="""I can help you create and manage your orders. \n\nTo control me use the following commands:
    \n\n <b>Managing Your Account:</b> \n /profile - editting your personal information \n\n <b>Vendors</b>"""+ retvendors()+""" \n\n <b>Orders</b> \n /viewcart - view your cart and checkout \n /trackorder - view your your order status \n /history - view your order history""", parse_mode=ParseMode.HTML)

def pprofile(bot, update):

    if bot.callback_query:
        chat_id = bot.callback_query.message.chat_id

    else:
        chat_id = bot.message.chat_id

    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': chat_id})

    user = response.json()

    if user.get('status'):
        gender = u"\U0001F6AB" if not user.get('gender', None) else user.get('gender')
        location = u"\U0001F6AB" if not user.get('location', None) else user.get('gender')

        keyboard = []
        keyboard.append([InlineKeyboardButton(u'Edit Location', callback_data='prof_location'), InlineKeyboardButton(u'Edit Gender', callback_data='prof_gender')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.bot.send_message(
            chat_id=chat_id,
            text="""<b>Edit your profile info.</b> \n\n <b>Gender: </b>"""+gender+ """\n <b>Location: </b>"""+location,
            parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    else:
        update.bot.send_message(
            chat_id=chat_id,
            text="Unable to retrieve profile at the moment."
        )

def processtext(bot, update):
    """Process user message."""
    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': bot.message.chat_id})
    user = response.json().get('status')

    if user:
        response = requests.get('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id})
        qtag = response.json()

        data_params = {
            'id': bot.message.chat_id,
        }

        if qtag.get('status') and qtag.get('tag') == 'prof_gender_new':
            gender = ['male', 'female', 'others']

            if str(bot.message.text).lower() in gender:

                data_params['type'] = 'gender',
                data_params['gender'] = str(bot.message.text).capitalize()

                response = requests.patch('http://127.0.0.1:8000/account/users/', params=data_params)
                up_user = response.json().get('status')

                if up_user:
                    bot.message.reply_text(text='Your gender has been updated successfully.')


                response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id, 'tag': 'prof_loc_new'})
                qt_up = response.json().get('status')

                if qt_up:
                    keyboard = [[KeyboardButton('Abuja'), KeyboardButton('Enugu'), KeyboardButton('Ekiti'), KeyboardButton('Lagos'), KeyboardButton('Ogun'), KeyboardButton('Port Harcourt')]]
                    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                    bot.message.reply_text(text='Send me your location to update your profile.', reply_markup=reply_markup)

            else:
                bot.message.reply_text(text='Invalid gender. Gender must either be (Male, Female or others).')

        if qtag.get('status') and qtag.get('tag') == 'prof_loc_new':
            location = ['lagos', 'ogun', 'ekiti', 'port harcourt', 'abuja', 'enugu']

            if str(bot.message.text).lower() in location:

                data_params['type'] = 'location',
                data_params['location'] = str(bot.message.text).capitalize()

                response = requests.patch('http://127.0.0.1:8000/account/users/', params=data_params)
                up_user_lc = response.json().get('status')

                if up_user_lc:
                    response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id, 'tag': 'none'})
                    qt_up_lc = response.json().get('status')
                    if qt_up_lc:
                        bot.message.reply_text(text='Your location has been updated successfully.')
                        bot.message.reply_text(text='<b>Profile setup complete</b>.', parse_mode=ParseMode.HTML)
                        help(bot, update)

            else:
                bot.message.reply_text(text='Invalid location. Location must either be (lagos, ogun, ekiti, port harcourt, abuja or enugu).')

        if qtag.get('status') and qtag.get('tag') == 'prof_gender':
            gender = ['male', 'female', 'others']

            if str(bot.message.text).lower() in gender:

                data_params['type'] = 'gender',
                data_params['gender'] = str(bot.message.text).capitalize()

                response = requests.patch('http://127.0.0.1:8000/account/users/', params=data_params)
                up_user = response.json().get('status')

                if up_user:
                    bot.message.reply_text(text='Your gender has been updated successfully.')


                response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id, 'tag': 'none'})
                response.json().get('status')

            else:
                bot.message.reply_text(text='Invalid gender. Gender must either be (Male, Female or others).')

        if qtag.get('status') and qtag.get('tag') == 'prof_location':
            location = ['lagos', 'ogun', 'ekiti', 'port harcourt', 'abuja', 'enugu']

            if str(bot.message.text).lower() in location:

                data_params['type'] = 'location',
                data_params['location'] = str(bot.message.text).capitalize()

                response = requests.patch('http://127.0.0.1:8000/account/users/', params=data_params)
                up_user_lc = response.json().get('status')

                if up_user_lc:
                    response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id, 'tag': 'none'})
                    qt_up_lc = response.json().get('status')
                    if qt_up_lc:
                        bot.message.reply_text(text='Your location has been updated successfully.')
            else:
                bot.message.reply_text(text='Invalid location. Location must either be (lagos, ogun, ekiti, port harcourt, abuja or enugu).')

        if qtag.get('status') and str(qtag.get('tag')).startswith('add_cart'):

            if str(bot.message.text).isnumeric():
                cartid = str(qtag['tag']).replace('add_cart_', '')

                response = requests.post('http://127.0.0.1:8000/order/', data={'id': int(cartid), 'chatid': bot.message.chat_id, 'qty': int(bot.message.text)})
                cart = response.json()

                if cart.get('status'):
                    bot.message.reply_text(text="<b>"+str(cart.get('qty'))+" "+str(cart.get('item'))+"</b> has been added to your cart", parse_mode=ParseMode.HTML)
                    response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id, 'tag': 'none'})
                    resp_cart = response.json().get('status')
                else:
                    bot.message.reply_text(text="Unable to add item to cart. Please try again later.",
                        parse_mode=ParseMode.HTML)

            else:
                bot.message.reply_text(text="Quantity must be an integer")

        if qtag.get('status') and str(qtag.get('tag'))=='trackorder':

            if str(bot.message.text).isnumeric():
                response = requests.get('http://127.0.0.1:8000/account/users/', params=data_params)
                chkuser = response.json().get('status')

                if chkuser:
                    response = requests.patch('http://127.0.0.1:8000/questiontag/question/',
                                              params={'id': bot.message.chat_id, 'tag': 'none'})
                    up_qt = response.json().get('status')

                    if up_qt:
                        bot.message.reply_text(
                            text="Searching for order: <b>"+ bot.message.text +"</b> please wait...", parse_mode=ParseMode.HTML)

                        orders(bot, update, bot.message.text)
            else:
                bot.message.reply_text(text="Order id can only be an integer number")

def processloc(bot, update):
    print(bot)

def processcmd(bot, update):

    if str(bot.message.text).startswith('/remove_'):
        response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id, 'tag': 'remove_cart'})
        qt_cart = response.json().get('status')

        if qt_cart:
            removeitem(bot, update, str(bot.message.text).replace('/remove_', ''))

    elif str(bot.message.text).startswith('/trackorder_'):
        orders(bot, update, str(bot.message.text).replace('/trackorder_', ''))

##########Vendors ###################################################

def selectvendor(bot, update):

    bot.message.reply_text(text="""<b>Select industry you will like to order from:</b> \n""" +retvendors(),
                           parse_mode=ParseMode.HTML)


def restaurant(bot, update):
    """Get restaurants within users locations"""
    chat_id = bot.message.chat_id

    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': chat_id})
    user = response.json()

    if user['status']:
        response = requests.get('http://127.0.0.1:8000/products/', params={'id': chat_id, 'type': 'restaurant'})
        vendor = response.json()

        if vendor['status']:
            keyboard = []
            temp_key = []

            for ven in vendor['vendor']:
                if len(temp_key) == 2:
                    keyboard.append(temp_key)
                    temp_key = []
                temp_key.append(InlineKeyboardButton(u''+str(ven[0]).capitalize(), callback_data='restaurant_'+str(ven[1]).lower()))

            if len(temp_key) != 0:
                keyboard.append(temp_key)
                temp_key = []

            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.message.reply_text(
                text="Please select the vendor you will like to order from",
                parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            bot.message.reply_text(
                text=vendor['message'],
                parse_mode=ParseMode.HTML)

def gadgets(bot, update):
    """Get gadgets within users locations"""
    chat_id = bot.message.chat_id

    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': chat_id})
    user = response.json()

    if user['status']:
        response = requests.get('http://127.0.0.1:8000/products/', params={'id': chat_id, 'type': 'gadgets'})
        vendor = response.json()

        if vendor['status']:
            keyboard = []
            temp_key = []

            for ven in vendor['vendor']:
                if len(temp_key) == 2:
                    keyboard.append(temp_key)
                    temp_key = []
                temp_key.append(InlineKeyboardButton(u''+str(ven[0]).capitalize(), callback_data='gadgets_'+str(ven[1]).lower()))

            if len(temp_key) != 0:
                keyboard.append(temp_key)
                temp_key = []

            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.message.reply_text(
                text="Please select the vendor you will like to order from",
                parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            bot.message.reply_text(
                text=vendor['message'],
                parse_mode=ParseMode.HTML)

def fashion(bot, update):
    """Get fashion within users locations"""
    chat_id = bot.message.chat_id

    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': chat_id})
    user = response.json()

    if user['status']:
        response = requests.get('http://127.0.0.1:8000/products/', params={'id': chat_id, 'type': 'fashion'})
        vendor = response.json()

        if vendor['status']:
            keyboard = []
            temp_key = []

            for ven in vendor['vendor']:
                if len(temp_key) == 2:
                    keyboard.append(temp_key)
                    temp_key = []
                temp_key.append(InlineKeyboardButton(u''+str(ven[0]).capitalize(), callback_data='fashion_'+str(ven[1]).lower()))

            if len(temp_key) != 0:
                keyboard.append(temp_key)
                temp_key = []

            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.message.reply_text(
                text="Please select the vendor you will like to order from",
                parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            bot.message.reply_text(
                text=vendor['message'],
                parse_mode=ParseMode.HTML)

#######################################################################

########################### Cart, Track order, History ##################

def removeitem(bot, update, value):
    chat_id = bot.message.chat_id

    response = requests.get('http://127.0.0.1:8000/questiontag/question/', params={'id': chat_id})
    qt_cart = response.json().get('status')

    if qt_cart:
        response = requests.patch('http://127.0.0.1:8000/order/', params={'id':value, 'chatid': chat_id})
        cart = response.json()

        if cart:
            update.bot.send_message(
                chat_id=chat_id,
                text="""Item has been successfully deleted""",
                parse_mode=ParseMode.HTML)
            viewcart(bot, update)
        else:
            update.bot.send_message(
                chat_id=chat_id,
                text=str(cart['message'])
            )
    response = requests.patch('http://127.0.0.1:8000/questiontag/question/', data={'id': bot.message.chat_id, 'tag': 'remove_cart'})

def checkoutitem(bot, update):
    chat_id = bot.message.chat_id

    response = requests.post('http://127.0.0.1:8000/order/checkout/', data={'id': chat_id})
    checkout = response.json()

    if checkout:
        update.bot.send_message(
            chat_id=chat_id,
            text=str(checkout['message']),
            parse_mode=ParseMode.HTML)
        trackorder(bot, update)
    else:
        update.bot.send_message(
            chat_id=chat_id,
            text=str(checkout['message'])
        )

def viewcart(bot, update):
    """View All items in carts and remove or checkout"""
    global dp
    chat_id = bot.message.chat_id

    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': chat_id})
    user = response.json()

    if user['status']:
        response = requests.get('http://127.0.0.1:8000/order/', params={'id': chat_id})
        cart = response.json()

        if cart['status']:
            keyboard = []
            text = """Item in cart: """+str(len(cart['cart']))+""" \n\n"""
            cnt = 1
            total = 0

            for cat in cart['cart']:
                update.dispatcher.add_handler(CommandHandler('remove_'+str(cat[0]), removeitem))
                text += str(cnt)+""". <b>"""+str(cat[2])+""" """+str(cat[1])+ """ - """+str(cat[4])+""" - """+str(cat[3])+"</b> \n "+ str(cat[2]) + " x "+ f"{float(cat[5]):,.2f}"+ " = "+f"{float(cat[6]):,.2f}"+" \n /remove_"+str(cat[0])+" \n\n"
                cnt += 1
                total += float(cat[6])

            text += """\n ---------------------------------- \n\t <b>Total</b>: """+ f"{float(total):,.2f}"
            keyboard.append([InlineKeyboardButton(u'removeall', callback_data='remove_all'), InlineKeyboardButton(u'checkout', callback_data='checkout')])

            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.message.reply_text(
                text=text,
                parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            bot.message.reply_text(
                text=cart['message'],
                parse_mode=ParseMode.HTML)

def trackorder(bot, update):

    response = requests.patch('http://127.0.0.1:8000/questiontag/question/', params={'id': bot.message.chat_id, 'tag': 'trackorder'})
    resp_cart = response.json()

    if resp_cart.get('status'):
        bot.message.reply_text(text="OK. Please provide me with your please provide me with your Order No. If you cannot remember your Order No, please click"+ u"\U0001F449"+ "/history", parse_mode=ParseMode.HTML)

def orders(bot, update, value):
    chatid = bot.message.chat_id
    orderid = int(value)

    response = requests.get('http://127.0.0.1:8000/order/checkout/', params={'id': chatid, 'orderid': orderid})
    orders = response.json()

    if orders.get('status'):
        items = ''.join(str(i)+". <b>"+n+"</b> \n\t\tQuantity: "+str(q)+"\n\t\tUnit Price:"+f" {float(p):,.2f}"+"\n\t\tAmount:"+ f"{float(a):,.2f}"+'\n\n' for i,n,q,p,a in orders.get('items'))

        text = "<b>Order #"+value+"</b>\nTotal item in Order: "+str(orders['t_item'])+" \nDate Ordered: "+ str(orders['date'])+"\nStatus: "+ str(orders['o_status']) +"\nPayment Mode: Cash \n\n"+items
        text += "=====================================\nDelivery Fee: "+f"{float(orders['delivery']):,.2f}"+"\nSubTotal: "+f"{float(orders['subtotal']):,.2f}"+"\n\nTotal: "+f"{float(orders['total']):,.2f}"

        bot.message.reply_text(
            text=text,
            parse_mode=ParseMode.HTML
        )

    else:
        bot.message.reply_text(text=str(orders['message']), parse_mode=ParseMode.HTML)

def history(bot, update):
    chat_id = bot.message.chat_id

    response = requests.get('http://127.0.0.1:8000/account/users/', params={'id': chat_id})
    user = response.json()

    if user['status']:
        response = requests.get('http://127.0.0.1:8000/order/history/', params={'id': chat_id})
        history = response.json()

        if history['status']:
            text = ''.join(f'{str(i)} - Order No. <b>{str(n)}</b> \nItems: {str(t)} \tPrice: {float(p):,.2f} \n'+u"\U0001F449"+f'/trackorder_{str(n)}\n\n' for i,n,t,p in history.get('history'))

            bot.message.reply_text(text='Your last top 10 orders are:', parse_mode=ParseMode.HTML)
            bot.message.reply_text(
                text=text,
                parse_mode=ParseMode.HTML)
        else:
            bot.message.reply_text(
                text=history['message'],
                parse_mode=ParseMode.HTML)
            help(bot, update)

###########################################################################

def main():
    """Start the bot"""
    global dp
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('profile', pprofile))

    dp.add_handler(CommandHandler('restaurant', restaurant))
    dp.add_handler(CommandHandler('gadgets', gadgets))
    dp.add_handler(CommandHandler('fashion', fashion))

    dp.add_handler(CommandHandler('viewcart', viewcart))
    dp.add_handler(CommandHandler('trackorder', trackorder))
    dp.add_handler(CommandHandler('history', history))

    dp.add_handler(CallbackQueryHandler(sortbutton))

    dp.add_handler(MessageHandler(Filters.command, processcmd))

    dp.add_handler(MessageHandler(Filters.location, processloc))
    dp.add_handler(MessageHandler(Filters.text, processtext))


    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()