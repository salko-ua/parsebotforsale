import re
from ast import Await

import requests
from aiogram import types
from aiogram.utils.media_group import MediaGroupBuilder
from bs4 import BeautifulSoup
from bs4.element import Tag


from main import bot


class Parser:
    def __init__(self, url):
        self.url = url
        self.response = requests.get(url)
        self.soup = BeautifulSoup(self.response.content, "html.parser")

    # Parse first 10 photo
    def get_photo(self, caption: str) -> list:
        # find all images tags in div
        wrapper = self.soup.find("div", class_="swiper-wrapper")
        if wrapper and isinstance(wrapper, Tag):
            images = wrapper.find_all("img")
        else:
            images = []
        
        # list with photo urls
        list_src_photo = []
        media_group = MediaGroupBuilder(caption=caption)
        
        # add urls to list
        for src in images:
            list_src_photo.append(src.get("src"))
        
        # if images more then 10 cut to 10
        if len(list_src_photo) > 10:
            del list_src_photo[10:]
        
        # add images_url to media_group
        for photo_url in list_src_photo:
            media_group.add_photo(media=photo_url)
        
        # return media_group (aiogram object)
        return media_group.build()

    # Parse main information like (amount of rooms, floor, area, region)
    def get_main_information(soup: BeautifulSoup) -> [str, str, str, str]:
        # constants to check the list "tags"
        need_words_ukrainian = [
            "Кількість кімнат:",
            "Загальна площа:",
            "Поверх:",
            "Поверховість:",
        ]
        need_words_russian = [
            "Количество комнат:",
            "Общая площадь:",
            "Этаж:",
            "Этажность:",
        ]

        checklist = []

        # find all span tags in div 
        div_with_tags = soup.find("div", class_="css-41yf00")
        if div_with_tags and isinstance(div_with_tags, Tag):
            tags = div_with_tags.find_all("span")
        else:
            tags = []
         
        # check for matches
        for need_word in need_words_russian:
            for tag in tags:
                if need_word in tag.text:
                    checklist.append(tag.text)

        for need_word in need_words_ukrainian:
            for tag in tags:
                if need_word in tag.text:
                    checklist.append(tag.text)
        
        # TODO переробити принцип
        try:
            if len(checklist) != 4:
                rooms = re.search(r"\d+", checklist[0]).group()
                area = re.search(r"\d+", checklist[1]).group()
                find_everything = re.search(r"\d+", checklist[2])
                flour = f"{find_everything.group()}"
            else:
                rooms = re.search(r"\d+", checklist[0]).group()
                area = re.search(r"\d+", checklist[1]).group()
                find_have = re.search(r"\d+", checklist[2])
                find_everything = re.search(r"\d+", checklist[3])
                flour = f"{find_have.group()} з {find_everything.group()}"
        except:
            rooms, area, flour = "", "", ""

        # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

        # we are looking for a district and a city, because
        # if there is no district, then the city is a district
        

        # TODO можливо можна шукати одразу в find? 
        find = soup.find_all("script")
        pattern_district = re.compile(r'\\"districtName\\":\\"([^\\"]+)\\"')
        pattern_city = re.compile(r'\\"cityName\\":\\"([^\\"]+)\\"')
        district, city = "", ""

        for one in find:
            district = pattern_district.search(one.text)
            city = pattern_city.search(one.text)
            if district and city:
                break

        if district:
            district = district.group(1)
        elif city:
            district = city.group(1)
        else:
            district = ""

        return rooms, flour, area, district

    def get_price(self) -> str:
        # parsing price from the page
        price = None
        tags_can_be = ["h2", "h3", "h4", "h5", "h6"]
        text_can_be = [re.compile(r".*грн.*"), re.compile(r".*\$.*")]
        
        ad_price_tag = self.soup.find("div", {"data-testid": "ad-price-container"})
        print(ad_price_tag)

        for tag in tags_can_be:
            for text in text_can_be:
                price = self.soup.find(tag, text=text)
                if price:
                    break

        if not price:
            return "Суму не знайдено"

        return price.text

    def delete_words(self, text: str, words_to_remove: list) -> str:
        # Використовуємо регулярний вираз для визначення слова з можливими крапками
        pattern = re.compile(
            r"\b(?:" + "|".join(map(re.escape, words_to_remove)) + r")\b", re.IGNORECASE
        )

        # Замінюємо відповідні слова на порожні рядки
        result = pattern.sub("", text)

        return result

    def get_header(self) -> str:
        # parsing caption from the page
        header = self.soup.find("h4", class_="css-yde3oc")
        header_test = self.soup.find("div", {"data-testid": "ad_title"})
        print(header_test)
        if not header:
            return "Заголовок не знайдено. Повідомте розробника про помилку."

        return header.text

    def get_caption(self) -> str:
        # parsing caption from the page
        caption = self.soup.find("div", class_="css-1o924a9")
        caption_test = self.soup.find("div", {"data-testid": "ad_description"})
        print(caption_test)
        if not caption:
            return "Опис не знайдено. Повідомте розробника про помилку."

        if len(caption.text) > 800:
            return caption.text[0:800]

        return caption.text

    def create_caption(self) -> str:
        words = [
            "Від",
            "От",
            "я собственник",
            "я власнник",
            "посредников",
            "своя",
            "свою",
            "риелтор",
            "риелторов",
            "агентство",
            "агент",
            "маклер",
            "посредник",
            "личную",
            "хозяин",
            "собственник",
            "собственника",
            "хозяина",
            "хозяйка",
            "без комиссии",
            "агента",
            "агентства",
            "собственников",
            "посередників",
            "своя",
            "свою",
            "ріелтор",
            "ріелторів",
            "агентство",
            "агент",
            "маклер",
            "посередник",
            "посередник",
            "особисту",
            "власник",
            "власника",
            "власників",
            "хазяїнахазяйка",
            "хазяйка",
            "особисту",
            "без комісії",
            "Без рієлторів",
            "комісій",
            "Без риелторов",
            "комисий",
            "комісіЇ",
            "комисии",
        ]

        caption = self.delete_words(self.get_caption(), words)
        header = self.delete_words(self.get_header(), words)

        rooms, flour, area, district = self.get_main_information()
        money = self.get_price()

        captions = (
            f"🏡{rooms}к кв\n" f"🏢Поверх: {flour}\n" f"🔑Площа: {area}м2\n" f"📍Район: {district}\n"
        )

        main_caption = f"💳️{money}" f"\n\n{header}\n\n" f"📝Опис:\n{caption}"
        if not rooms != "":
            return main_caption
        return captions + main_caption


# Отримання всіх даних і запуск надсилання
async def get_data(message: types.Message):
    soup = Parser(message.text)
    caption = soup.create_caption()
    photo_group = soup.get_photo(caption)
    new_photo_group = photo_group.copy()


    for i in range(len(photo_group)):
        try:
            message_photo = await bot.send_media_group(chat_id=-1001902595324, message_thread_id=805, media=[photo_group[i]])
            await bot.delete_message(message_id=message_photo[0].message_id, chat_id=-1001902595324)
        except Exception as e:
            new_photo_group.remove(photo_group[i])
    await message.answer_media_group(media=new_photo_group)
