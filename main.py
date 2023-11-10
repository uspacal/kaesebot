from openai import OpenAI
import discord
from discord.ext import commands
import tiktoken
import json

def count_tokens(text, encoding_name='cl100k_base'):
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def openai_request(prompt: str):
    client = OpenAI(
        organization='<ORGANIZATION>',
        api_key = '<API-KEY>'
    )
    assistent = "You are a helpful assistant."
    prompt_token = count_tokens(prompt)
    assistent_token = 17
    price_per_token = 0.002 / 1000
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": assistent},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4097 - prompt_token - assistent_token
    )
    
    price = response.usage.total_tokens * price_per_token
    
    return response.choices[0].message.content, price


async def send_long(ctx: discord.ext.commands.Context, message: str):
    if len(message) > 2000:
        await ctx.send(message[:2000])
        await send_long(ctx, message[2000:])
    else:
        await ctx.send(message)


async def command_ai(ctx: discord.ext.commands.Context, prompt):
    await ctx.message.add_reaction("⌛")
    try:
        response, price = openai_request(prompt)
        log(ctx.author.id, ctx.author.name, price)
        await send_long(ctx, f'`Prompt={prompt}`\n`Price=${round(price, 6)}`\n' + response.strip())

    except Exception as err:
        print(err)
        await ctx.message.clear_reaction('⌛')
        await ctx.message.add_reaction("❌")
        await ctx.send(f'```\n{err}\n```')
    else:
        await ctx.message.clear_reaction('⌛')
        await ctx.message.add_reaction("✔")


def log(user_id: str, username: str, price: float):
    json_filename = 'data.json'
    try:
        with open(json_filename, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {}

    # Check if the user already exists in the data
    if user_id in data:
        # If the user exists, update the value
        data[user_id]['value'] += price
        data[user_id]['usage'] += 1
    else:
        # If the user doesn't exist, add a new entry
        data[user_id] = {'username': username, 'value': price, "usage": 1}

    # Write the updated data back to the JSON file
    with open(json_filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def check_channel(ctx: discord.ext.commands.Context, name):
    try:
        if ctx.channel.name == name:
            return True, ctx.channel.name
        else: return False, ctx.channel.name
    except Exception as err:
        print(err)
        return False, 'here'


if __name__ == '__main__':
    bot_token = '<BOT_TOKEN>'
    
    intents = discord.Intents.default()
    intents.reactions = True
    intents.messages = True
    intents.message_content = True

    bot_prefix = "!"
    bot = commands.Bot(command_prefix=bot_prefix, intents=intents)


    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user.name} ({bot.user.id})")


    @bot.command()
    async def ping(ctx):
        await ctx.send("Pong!")


    @bot.command()
    async def ai(ctx, *, message):
        boo, name = check_channel(ctx, 'kaesebot')
        if boo:
            await command_ai(ctx, message)
        else:
            await ctx.message.add_reaction("❌")
            await ctx.send(f"I do not operate in '{name}' :(")


    bot.run(bot_token)
