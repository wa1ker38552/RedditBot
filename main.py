from discord.ext import commands
from alive import keepAlive
from replit import db
import requests
import discord
import json
import os

# database
# db['config'] = {}
watching_messages = {}

client = commands.Bot(command_prefix='.', help_command=None)

def get_post(subreddit):
  request = requests.get(f'https://reddit.com/r/{subreddit}/random.json', 
                         headers={'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}).json()

  if db['config']['695397172169932831']['logging'] is True:
    with open('raw.json','w') as file:
      file.write(json.dumps(request[0]['data']['children'][0]['data'], indent=3))
    
  post_data = {}
  data = request[0]['data']['children'][0]['data']
  
  post_data['title'] = data['title']
  post_data['author'] = data['author']
  post_data['comments'] = data['num_comments']
  post_data['description'] = data['selftext'] if data['selftext'] != 'None' else ''
  post_data['votes'] = data['ups']
  post_data['ratio'] = data['upvote_ratio']
  post_data['url'] = data['url']
  post_data['link'] = f'https://reddit.com{data["permalink"]}'
  
  return post_data

def create_embed(subreddit):
  embed = discord.Embed()

  post = get_post(subreddit)
  if len(post['title']) > 265:
    embed.title = ' '.join(post['title'].split()[:-2])+'...'
  else:
    embed.title = post['title']
  embed.url = post['link']
  embed.description = f'''
  {post['description']}
  
  <:reddit_comment:1008046654445850655> {post['comments']}   <:reddit_upvote:1008046676965077063> {post['votes']}   <:reddit_percentage:1008051810113687622> {post['ratio']}  <:reddit_author:1008052557731606569> {post['author']}
  
  '''
  
  embed.color = 0xff4500
  embed.set_image(url=post['url'])

  return embed

def set_default_message(message):
  db['config'][str(message.author.id)] = {'hide': False, 'logging': True}
def set_default_context(ctx):
  db['config'][str(ctx.message.author.id)] = {'hide': False, 'logging': True}

@client.event
async def on_ready():
  print(client.user)

@client.event
async def on_reaction_add(reaction, user):
  if not user == client.user:
    if reaction.message.id in watching_messages:
      if reaction.emoji == '⏭️':
        embed = create_embed(watching_messages[reaction.message.id][1])
        
        await watching_messages[reaction.message.id][0].clear_reactions()
        await watching_messages[reaction.message.id][0].edit(embed=embed)
        await watching_messages[reaction.message.id][0].add_reaction('⏭️')
        await watching_messages[reaction.message.id][0].add_reaction('🗑️')

      elif reaction.emoji == '🗑️':
        await watching_messages[reaction.message.id][0].delete()

@client.event
async def on_message(message):
  if message.content[:2] == 'r/':
    if str(message.author.id) in db['config']:
      if db['config'][str(message.author.id)]['hide'] is True:
        await message.delete()
    else:
      set_default_message(message)  
      
    try:
      embed = create_embed(message.content[2:])

      embed = await message.channel.send(embed=embed)
      await embed.add_reaction('⏭️')
      await embed.add_reaction('🗑️')

      # stores message id as key, and embed + subreddit in a list as value
      watching_messages[embed.id] = [embed, message.content[2:]]
    
    except KeyError:
      embed = discord.Embed()
      embed.title = 'Subreddit Not Found!'
      embed.color = 0xff4500
  
      await message.channel.send(embed=embed)
  else:
    await client.process_commands(message)

@client.command()
async def help(ctx):
  embed = discord.Embed()
  embed.title = 'RedditBot Help'
  embed.color = 0xff4500
  embed.description = '''
  RedditBot is a Discord bot meant to help you browse Reddit posts from Discord! To get started, use `r/{subreddit}` to search for a post. Once RedditBot sends a post, there will be 2 additional reactions, one will skip the post onto another random post and the other will delete the post.

  Commands:
  `r/{subreddit}`: Shows random subreddit post
  
  `.help`: Help page
  `.config`: Shows your config page
  `.config {category} {bool}`: Sets config category to True or False
  '''

  await ctx.send(embed=embed)

@client.command()
async def deleteall(ctx):
  if str(ctx.message.author.id) in db['config']:
    if db['config'][str(ctx.message.author.id)]['hide'] is True:
      await ctx.message.delete()
  else:
    set_default_context(ctx)
    
  for message in watching_messages:
    await watching_messages[message][0].delete()

@client.command()
async def config(ctx, parameter=None, bool=None):
  if parameter is None and bool is None:

    if str(ctx.message.author.id) in db['config']: pass
    else:
      set_default_context(ctx)

    items = []
    for key in db['config'][str(ctx.message.author.id)]:
      items.append(f"{key}: {db['config'][str(ctx.message.author.id)][key]}")
    await ctx.send('```py\n'+'\n'.join(items)+'```')
      
  if parameter == 'hide':
    if str(ctx.message.author.id) in db['config']:
      db['config'][str(ctx.message.author.id)]['hide'] = bool in ['true']
    else:
      set_default_context(ctx)
      db['config'][str(ctx.message.author.id)]['hide'] = bool in ['true']
      
    await ctx.send(f'Succesfully set hide config to {bool in ["true"]}')

  elif parameter == 'logging':
    if str(ctx.message.author.id) in db['config']:
      db['config'][str(ctx.message.author.id)]['logging'] = bool in ['true']
    else:
      set_default_context(ctx)
      db['config'][str(ctx.message.author.id)]['logging'] = bool in ['true']

    await ctx.send(f'Succesfully set logging config to {bool in ["true"]}')


keepAlive()
client.run(os.environ['token'])
