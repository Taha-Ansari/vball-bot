from dotenv import load_dotenv
import discord
import os
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
bot = discord.Bot(intents=intents)
load_dotenv()

VBALL_ROLL_ID = os.getenv('VBALL_ROLL_ID')
BOOKER_ID = os.getenv('BOOKER_ID')
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))
WEDNESDAY_NUM = 2
TIME_LIMIT_IN_HOURS = 72
MIN_NUM_PLAYERS = 10
EMOJI_COUNT_MAP = {'👍': 1, '1️⃣': 1, '2️⃣': 2, '3️⃣': 3, '4️⃣': 4,
                   '5️⃣': 5, '6️⃣': 6, '7️⃣': 7, '8️⃣': 8, '9️⃣': 9,
                   '🔟': 10
                   }
CURRENT_MSG_ID = 0

# Helper functions #


def get_next_sunday():
    today = datetime.today()
    sunday = today + timedelta((6-today.weekday()) % 7)
    return sunday


def get_poll_text():
    next_sunday = get_next_sunday()
    date = next_sunday.strftime('%B') + " " + next_sunday.strftime('%d')
    estimated_time = '3pm-5pm'
    location = 'Milton Sports Center'
    estimated_cost = 9

    poll = f'''
  <@{VBALL_ROLL_ID}> Who would like to play volleyball this Sunday **({date})?**

  **Estimated Time:** {estimated_time}
  **Location:** {location}
  **Estimated Cost:** ${estimated_cost}

  *Minimum {MIN_NUM_PLAYERS} upvotes required before booking criteria met.*
  '''
    return poll

# Bot Command Functions #


@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user}")
    await schedule_weekly_poll()


@bot.command()
async def collect_vball_money(ctx, amount):
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    await channel.send(f"<@{VBALL_ROLL_ID}> Thanks for coming! For those that came please etransfer ${amount} to taha-ansari@hotmail.com")
    print("[Message] Collect message sent")
    await ctx.respond("Collect message sent", ephemeral=True)


@bot.command()
async def bot_say(ctx, message):
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    await channel.send(f"<@{VBALL_ROLL_ID}> {message}")
    print(f"[Message] Message sent: {message}")
    await ctx.respond("bot_say message sent", ephemeral=True)


@bot.command()
async def update_last_post(ctx, day, date, time, location, cost):
    global CURRENT_MSG_ID
    if CURRENT_MSG_ID != 0:
        latest_poll_msg = await ctx.fetch_message(CURRENT_MSG_ID)
        content = f'''
  <@{VBALL_ROLL_ID}> Who would like to play volleyball this {day} **({date})?**

  **Estimated Time:** {time}
  **Location:** {location}
  **Estimated Cost:** ${cost}

  *Minimum {MIN_NUM_PLAYERS} upvotes required before booking criteria met.*
  '''
        await latest_poll_msg.edit(content=content)
        print(f"[Update] Post update")
        await ctx.respond("Post updated", ephemeral=True)
    else:
        print(f"[Update] Post not found")
        await ctx.respond("Post not found", ephemeral=True)


async def post_and_monitor_poll(channel):
    poll_msg = await channel.send(get_poll_text())
    global CURRENT_MSG_ID
    CURRENT_MSG_ID = poll_msg.id
    criteria_not_met = True
    due_date = datetime.now() + timedelta(hours=TIME_LIMIT_IN_HOURS)
    while (criteria_not_met):
        upvotes = 0
        await asyncio.sleep(5)
        poll_fetch = await poll_msg.channel.fetch_message(CURRENT_MSG_ID)
        # Calculate current upvotes every 5 seconds
        for reaction in poll_fetch.reactions:
            if reaction.emoji in EMOJI_COUNT_MAP:
                upvotes += reaction.count * EMOJI_COUNT_MAP[reaction.emoji]
                print(f'[Monitoring Mode] current upvotes: {upvotes}')
            # Check if upvotes criteria has been met
            if upvotes >= MIN_NUM_PLAYERS:
                print(
                    f'[Message] Criteria has been met! <@{BOOKER_ID}> has been notified to book the court')
                await channel.send(f'Criteria has been met! <@{BOOKER_ID}> has been notified to book the court')
                criteria_not_met = False
                break
        # Cancel post if not enough votes before due date target time
        if datetime.now() + timedelta(seconds=0) > due_date:
            print(
                f'[Message] <@{VBALL_ROLL_ID}> Not enough votes within {TIME_LIMIT_IN_HOURS} hours, no vball this weekend!')
            await channel.send(f'<@{VBALL_ROLL_ID}> Not enough votes within {TIME_LIMIT_IN_HOURS} hours, no vball this weekend!')
            criteria_not_met = False
            break


async def schedule_weekly_poll():
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    while True:
        # Check to see if it's a wednesday (Mon: 0, Wed: 2, Sunday: 6)
        day = datetime.today().weekday()
        if day == WEDNESDAY_NUM:
            now = datetime.now()
            target = now.replace(hour=16, minute=0, second=0)
            wait_time = (target-now).total_seconds()
            if wait_time >= 0:
                print(
                    f"[Sleep] It is {now} | target time is {target} | sleeping for {wait_time} seconds ...")
                await asyncio.sleep(wait_time)
                await post_and_monitor_poll(channel)
            else:
                print(
                    f"[Sleep] It is {now} but post should be already made. Sleeping till next wed ...")
                await sleep_till_next_wed()
        else:
            print(f"[Sleep] It is not Wed. Sleeping till next wed ...")
            await sleep_till_next_wed()


async def sleep_till_next_wed():
    today = datetime.today()
    if today.weekday() == 2:
        days_ahead = 7
    else:
        days_ahead = (2-today.weekday()) % 7
    next_wed = today + timedelta(days_ahead)
    # Bot needs to exit sleep next wed at 1am
    next_wed = next_wed.replace(hour=1, minute=0, second=0)
    now = datetime.now()
    wait_time = (next_wed-now).total_seconds()
    print(
        f"[Sleep] Target wake day is {next_wed} | Sleeping for {wait_time} seconds ...")
    await asyncio.sleep(wait_time)

# Main
if __name__ == '__main__':
    bot.run(os.getenv('API_TOKEN'))
