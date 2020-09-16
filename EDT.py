# EDT.py

import discord
from discord.ext import commands

import requests, json, html, re
from datetime import datetime, timedelta

# Just a check to limit these commands to the authorized guilds
def usage_check(ctx):
    authorized_guilds = [688084158026743816, 705373935243362347, 710518367253168199]
    return ctx.guild.id in authorized_guilds

# Main request function, return a formatted array of modules (dicts)
# @start_date @end_date : First and last day of the requested calendar
# @TD : Group class
def request_td_edt(start_date, end_date, TD):
    url = 'https://edt.uvsq.fr/Home/GetCalendarData'
    TDList = ["S5 INFO TD 1","S5 INFO TD 2","S5 INFO TD 3","S5 INFO TD 4"]
    global_edt = []

    data = {'start':start_date,'end':end_date,'resType':'103','calView':'agendaDay','federationIds[]':TDList[TD]}
    response = requests.post(url,data=data)
    bytes_value = response.content.decode('utf8')
    data = json.loads(bytes_value)

    # Formatting data loaded into a simple dict
    modules = []
    for module_data in data:
        debut = datetime.strptime(module_data["start"], "%Y-%m-%dT%H:%M:%S")
        fin = datetime.strptime(module_data["end"], "%Y-%m-%dT%H:%M:%S")
        # Re-formatting the 'description' HTML field (pretty odd job)
        description = html.unescape(module_data["description"])
        description = description.replace("\n", "")
        description = description.replace("\r", "")
        description = description.replace("<br />", "¨")

        sub_data = {
            "jour":f'{debut.day}/{debut.month}',
            "horaire":'{:0>2d}:{:0>2d}  —  {:0>2d}:{:0>2d}'.format(debut.hour, debut.minute, fin.hour, fin.minute),
            "type":description.split("¨")[0],
            "salle":description.split("¨")[1],
            "module":description.split("¨")[2],
            "groupes":description.split("¨")[3]
        }
        modules.append(sub_data)
    # Sort the modules array by in ascending order of schedules
    modules = sorted(modules, key=lambda sub_data: sub_data["horaire"])
    return modules

# Return a specific thumbnail for each @weekday
def url_jour(weekday):
    if weekday == 0 : return "https://img.icons8.com/officel/2x/monday.png"
    if weekday == 1 : return "https://img.icons8.com/officel/2x/tuesday.png"
    if weekday == 2 : return "https://img.icons8.com/officel/2x/wednesday.png"
    if weekday == 3 : return "https://img.icons8.com/officel/2x/thursday.png"
    if weekday == 4 : return "https://img.icons8.com/officel/2x/friday.png"
    if weekday == 5 : return "https://img.icons8.com/officel/2x/saturday.png"
    if weekday == 6 : return "https://img.icons8.com/officel/2x/sunday.png"

# Return a french formatted date from a @start_date
def jour_de_la_semaine(start_date):
    weekday = start_date.weekday()
    day = ""
    if weekday == 0 : day = "Lundi"
    if weekday == 1 : day = "Mardi"
    if weekday == 2 : day = "Mercredi"
    if weekday == 3 : day = "Jeudi"
    if weekday == 4 : day = "Vendredi"
    if weekday == 5 : day = "Samedi"
    if weekday == 6 : day = "Dimanche"

    return "{} {:0>2d}/{:0>2d}".format(day, start_date.day, start_date.month)

# Interpret the @daydate from the user's command and return two datetime objects @start_date & @end_date
def date_formatting(daydate):
    # start_date = str(datetime.now())[:10] if daydate == None else '2020-{}-{}'.format(daydate.split("/")[1], daydate.split("/")[0])
    if daydate == None:
        start_date = str(datetime.now())[:10]
    elif int(daydate.split("/")[1]) > 9:
        start_date = '2020-{}-{}'.format(daydate.split("/")[1], daydate.split("/")[0])
    else:
        start_date = '2021-{}-{}'.format(daydate.split("/")[1], daydate.split("/")[0])

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = start_date + timedelta(days=0)
        return start_date, end_date
    except Exception as e:
        return -1

# EDT Cog Class
class EDT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Return the calendar for a @TD Group and a given @daydate (default: today date)
    @commands.command(name="day")
    async def day(self, ctx, TDGR : str, daydate : str = None):
        if not usage_check(ctx):
            print("EDT usage on the wrong guild.")
            return

        TD = int(re.sub(r'[^1-4]', '', TDGR))

        if isinstance(date_formatting(daydate), int):
            await ctx.send("La date {} n'est pas valide !".format(daydate))
            return
        else:
            start_date, end_date = date_formatting(daydate)

        modules = request_td_edt(start_date, end_date, TD-1)

        desc = "{} créneaux ce jour".format(len(modules)) if len(modules) > 0 else 'Journée libre !'
        if len(modules) == 1 : desc = "{} créneau ce jour".format(len(modules))

        embed = discord.Embed(title="<:week:755154675149439088> TD{} — {}".format(TD, jour_de_la_semaine(start_date)), description=desc, color=0x3b8ea7)
        for module in modules:
            embed.add_field(name=module["horaire"], value="{}\n{} | {}\n".format(module["module"][2:len(module["module"])-11], module["type"], module["salle"]) + u"\u2063", inline=False)
        embed.set_thumbnail(url=url_jour(start_date.weekday()))
        embed.set_footer(text="Dernière actualisation : {}".format(str(datetime.now())[:16]), icon_url=self.bot.user.avatar_url)
        await ctx.channel.send(embed=embed)

    # Return the week calendar for a @TD Group and a given @daydate (default: today date)
    @commands.command(name="week")
    async def week(self, ctx, TDGR : str, daydate : str = None):
        if not usage_check(ctx):
            print("EDT usage on the wrong guild.")
            return

        TD = int(re.sub(r'[^1-4]', '', TDGR))

        if isinstance(date_formatting(daydate), int):
            await ctx.send("La date {} n'est pas valide !".format(daydate))
            return
        else:
            start_date, end_date = date_formatting(daydate)

        while start_date.weekday() < 5:
            end_date = start_date + timedelta(days=0)
            modules = request_td_edt(start_date, end_date, TD-1)

            desc = "{} créneaux ce jour".format(len(modules)) if len(modules) > 0 else 'Journée libre !'
            if len(modules) == 1 : desc = "{} créneau ce jour".format(len(modules))

            embed = discord.Embed(title="<:week:755154675149439088> TD{} — {}".format(TD, jour_de_la_semaine(start_date)), description=desc, color=0x3b8ea7)
            for module in modules:
                embed.add_field(name=module["horaire"], value="{}\n{} | {}\n".format(module["module"][2:len(module["module"])-11], module["type"], module["salle"]) + u"\u2063", inline=False)
            embed.set_thumbnail(url=url_jour(start_date.weekday()))
            embed.set_footer(text="Dernière actualisation : {}".format(str(datetime.now())[:16]), icon_url=self.bot.user.avatar_url)
            await ctx.channel.send(embed=embed)
            start_date = start_date + timedelta(days=1)

    # Just some error sended warnings
    @week.error
    @day.error
    async def test_on_error(self, ctx, error):
        await ctx.send("*{}*\n`{}{} [TD] [day/month]`".format(error, ctx.prefix, ctx.command))

def setup(bot):
    bot.add_cog(EDT(bot))
