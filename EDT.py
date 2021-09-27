import discord
from discord.ext import commands

import requests, json, html, re
from datetime import datetime, timedelta

# Remote course: Displaying Zoom links with the calendar
zoom_links = {
    "IN603":     "https://uvsq-fr.zoom.us/j/XXXXXXXXX?pwd=XXXXXXXXXXXXXXXXX",
    "IN606_TD1": "https://uvsq-fr.zoom.us/j/XXXXXXXXX?pwd=XXXXXXXXXXXXXXXXX"
}

# Just a check to limit these commands to the authorized guilds
def usage_check(ctx):
    authorized_guilds = [688084158026743816, 705373935243362347, 710518367253168199]
    return ctx.guild.id in authorized_guilds

# Main request function, return a formatted array of modules (dicts)
# @start_date @end_date : First and last day of the requested calendar
# @TD : Group class
def request_td_edt(start_date, end_date, TD, LIC):
    url = 'https://edt.uvsq.fr/Home/GetCalendarData'
    if LIC == 3:
        # TODO: Automate even/odd semester's deduction
        TDList = ["S6 INFO TD01","S6 INFO TD02","S6 INFO TD03","S6 INFO TD04"]
    elif LIC == 2:
        TDList = ["S4 INFO TD01","S4 INFO TD02","S4 INFO TD03","S4 INFO TD04"]
    else: # M1
        TDList = ["M1 SECRETS", "M1 AMIS", "M1 SECRETS", "M1 SECRETS"]


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

        # Remote course: We don't append the on-moodle-TD to avoid the double displaying
        if "TD" in sub_data["type"] and "MOODLE" in sub_data["salle"]:
            continue
        else:
            modules.append(sub_data)

    # Sort the modules array by in ascending order of schedules
    modules = sorted(modules, key=lambda sub_data: sub_data["horaire"])
    
    # Remote course: Adding zoom CM & TD links next to Module's names
    for module in modules:
        module["module"] = module["module"][:len(module["module"])-11]
        # if 'CM' in  module['type']:
        #     for zm in zoom_links:
        #         if zm in module['module']:
        #             module['module'] += f"\n[Lien Zoom disponible!]({zoom_links[zm]})"
   
        # elif 'TD' in module['type']:
        #     formatted = f"{module['module'][:5]}_TD{TD+1}"
        #     if formatted in zoom_links:
        #         module['module'] += f"\n[Lien Zoom disponible!]({zoom_links[formatted]})"


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

def calculate_duration(modules):
    # TODO: Calculate total courses duration for a given day 
    return 'X'

# Interpret the @daydate from the user's command and return two datetime objects @start_date & @end_date
def date_formatting(daydate):
    # start_date = str(datetime.now())[:10] if daydate == None else '2020-{}-{}'.format(daydate.split("/")[1], daydate.split("/")[0])
    if daydate == None:
        start_date = str(datetime.now())[:10]
    elif int(daydate.split("/")[1]) > 8:
        # TODO: Automate the current year's deduction
        start_date = '2021-{}-{}'.format(daydate.split("/")[1], daydate.split("/")[0])
    else:
        start_date = '2022-{}-{}'.format(daydate.split("/")[1], daydate.split("/")[0])

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = start_date + timedelta(days=0)
        return start_date, end_date
    except Exception as e:
        return -1

# Remote course: checks and returns the actual week  
# def get_semaine(modules):
#     for module in modules:
#         if "TD" in module["type"]:
#             if "A" in module["groupes"]:
#                 return "Semaine A"
#             else:
#                 return "Semaine B"
#     return ""

def get_m1_group(module):
    if 'gr 1' in module["groupes"]:
        return "TD1"
    elif 'gr 2' in module["groupes"]:
        return "TD2"
    elif 'gr 3' in module["groupes"]:
        return "TD3"
    else:
        return "None"


async def send_day_edt(self, ctx, TDGR, daydate, LIC):
    TD = int(re.sub(r'[^1-4]', '', TDGR))

    if isinstance(daydate, str):
        if isinstance(date_formatting(daydate), int):
            await ctx.send("La date {} n'est pas valide !".format(daydate))
            return
        else:
            start_date, end_date = date_formatting(daydate)
    else:
        start_date = daydate
        end_date = start_date + timedelta(days=0)

    
    modules = request_td_edt(start_date, end_date, TD-1, LIC)
    
    # semaine = get_semaine(modules)
    # desc = "**{}** — {} créneaux ce jour".format(semaine, len(modules)) if len(modules) > 0 else 'Journée libre !'
    # if len(modules) == 1 : desc = "**{}** — {} créneau ce jour".format(semaine, len(modules))
    
    if LIC == 1:
        lic_txt = 'M1 Info'
    elif LIC == 2:
        lic_txt = 'L2 Info'
    elif LIC == 3:
        lic_txt = 'L3 Info'
    
    duration = calculate_duration(modules)

    desc = f"{len(modules)} créneaux ce jour — {duration} heures au total" if len(modules) > 0 else 'Journée libre !'
    if len(modules) == 1 : desc = f"{len(modules)} créneau ce jour"
    
    embed = discord.Embed(title="<:week:887402631482474506> {} TD{} — {}".format(lic_txt, TD, jour_de_la_semaine(start_date)), description=desc, color=0x3b8ea7, timestamp=datetime.utcnow())
    embed.set_thumbnail(url=url_jour(start_date.weekday()))
    embed.set_footer(text="Dernière actualisation", icon_url=self.bot.user.avatar_url)
    
    if LIC == 1: # M1
        for module in modules:
            if "TD" in module["type"]:
                tdgrp = get_m1_group(module)
                embed.add_field(name=module["horaire"], value=f"{module['module']}\n<:L3:881594439552860281> **{tdgrp}** | {module['salle']}\n", inline=False)
            else:
                embed.add_field(name=module["horaire"], value="{}\n<:M1:881594437585752085> **{}** | {}\n".format(module["module"], module["type"], module["salle"]) + u"\u2063", inline=False)
    
    else: # TODO: L3 & L2 daily and weekly calendar
        for module in modules:
            if "TD" in module["type"]:
                if "A" in module["groupes"]:
                    embed.add_field(name=module["horaire"], value="{}\n{} | {}\n❯ Sous-groupe B en distanciel\n".format(module["module"], module["type"], module["salle"]) + u"\u2063", inline=False)
                else:
                    embed.add_field(name=module["horaire"], value="{}\n{} | {}\n❯ Sous-groupe A en distanciel\n".format(module["module"], module["type"], module["salle"]) + u"\u2063", inline=False)
            else:
                embed.add_field(name=module["horaire"], value="{}\n{} | {}\n".format(module["module"], module["type"], module["salle"]) + u"\u2063", inline=False)
    
    await ctx.channel.send(embed=embed)


# EDT Cog Class
class EDT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Return the calendar for a @TD Group and a given @daydate (default: today date)
    @commands.command(name="dayl3")
    async def dayl3(self, ctx, TDGR : str, daydate : str = None):
        if not usage_check(ctx):
            print("EDT usage on the wrong guild.")
            return

        await send_day_edt(self, ctx, TDGR, daydate, 3)
    
    @commands.command(name="dayl2")
    async def dayl2(self, ctx, TDGR : str, daydate : str = None):
        if not usage_check(ctx):
            print("EDT usage on the wrong guild.")
            return

        await send_day_edt(self, ctx, TDGR, daydate, 2)

    @commands.command(name="daym1")
    async def daym1(self, ctx, daydate : str = None):
        if not usage_check(ctx):
            print("EDT usage on the wrong guild.")
            return

        await send_day_edt(self, ctx, '1', daydate, 1)
        
    
    # Return the week calendar for a @TD Group and a given @daydate (default: today date)
    @commands.command(name="weekm1")
    async def weekm1(self, ctx, daydate : str = None):
        if not usage_check(ctx):
            print("EDT usage on the wrong guild.")
            return

        # TD = int(re.sub(r'[^1-4]', '', TDGR))

        if isinstance(date_formatting(daydate), int):
            await ctx.send("La date {} n'est pas valide !".format(daydate))
            return
        else:
            start_date, end_date = date_formatting(daydate)
        
        while start_date.weekday() < 5:
            # end_date = start_date + timedelta(days=0)
            
            await send_day_edt(self, ctx, '1', start_date, 1)
            start_date = start_date + timedelta(days=1)

            # modules = request_td_edt(start_date, end_date, TD-1, LIC)
            
            # semaine = get_semaine(modules)
            # desc = "**{}** — {} créneaux ce jour".format(semaine, len(modules)) if len(modules) > 0 else 'Journée libre !'
            # if len(modules) == 1 : desc = "**{}** — {} créneau ce jour".format(semaine, len(modules))
            
            
            # embed = discord.Embed(title="<:week:887402631482474506> TD{} — {}".format(TD, jour_de_la_semaine(start_date)), description=desc, color=0x3b8ea7)

            # for module in modules:
            #     if "TD" in module["type"]:
            #         if "A" in module["groupes"]:
            #             embed.add_field(name=module["horaire"], value="{}\n{} | {}\n❯ Sous-groupe B en distanciel\n".format(module["module"], module["type"], module["salle"]) + u"\u2063", inline=False)
            #         else:
            #             embed.add_field(name=module["horaire"], value="{}\n{} | {}\n❯ Sous-groupe A en distanciel\n".format(module["module"], module["type"], module["salle"]) + u"\u2063", inline=False)
            #     else:
            #         embed.add_field(name=module["horaire"], value="{}\n{} | {}\n".format(module["module"], module["type"], module["salle"]) + u"\u2063", inline=False)
            # embed.set_thumbnail(url=url_jour(start_date.weekday()))
            # embed.set_footer(text="Dernière actualisation {}".format(str(datetime.now())[:16]), icon_url=self.bot.user.avatar_url)
            # await ctx.channel.send(embed=embed)
            
            # start_date = start_date + timedelta(days=1)


    # Just some error sended warnings
    @weekm1.error
    @dayl2.error
    @dayl3.error
    @daym1.error
    async def test_on_error(self, ctx, error):
        await ctx.send("*{}*\n`{}{} [TD] [day/month]`".format(error, ctx.prefix, ctx.command))

def setup(bot):
    bot.add_cog(EDT(bot))
