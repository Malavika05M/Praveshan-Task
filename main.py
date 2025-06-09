import discord
from discord.ext import commands
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
import json
import random

# Load environment variable
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

class GeniusScraper:
    def __init__(self):
        self.base_url = "https://genius.com"
        self.search_url = "https://genius.com/search"
        self.headerszz = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Brave/131.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = None

    async def create_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def search_song(self, query):
        """Search for a song on Genius with improved selectors"""
        await self.create_session()
        
        try:
            params = {'q': query}
            async with self.session.get(self.search_url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Try multiple selector patterns
                    patterns = [
                        ('a', {'class': 'mini_card'}),
                        ('a', {'href': re.compile(r'/.*-lyrics$')}),
                        ('div', {'class': 'search_result'}),
                        ('a', {'class': 'song_link'})
                    ]
                    
                    for tag, attrs in patterns:
                        search_results = soup.find_all(tag, attrs)
                        if search_results:
                            for result in search_results:
                                href = result.get('href')
                                if href and href.startswith('/'):
                                    return self.base_url + href
                    
                    # If no results found with patterns, try fallback
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        if '-lyrics' in link['href']:
                            return self.base_url + link['href']
                            
        except Exception as e:
            print(f"Search error: {e}")
            return None
        
        return None

    async def get_song_lyrics(self, song_url):
        """Extract lyrics with improved parsing"""
        await self.create_session()
        
        try:
            async with self.session.get(song_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Try multiple lyric container patterns
                    patterns = [
                        {'data-lyrics-container': 'true'},
                        {'class': re.compile(r'lyrics|Lyrics__Container')},
                        {'class': 'lyrics'},
                        {'class': 'song_body-lyrics'}
                    ]
                    
                    for pattern in patterns:
                        lyrics_div = soup.find('div', pattern)
                        if lyrics_div:
                            # Remove unwanted elements
                            for br in lyrics_div.find_all('br'):
                                br.replace_with('\n')
                            for script in lyrics_div.find_all('script'):
                                script.decompose()
                            
                            lyrics = lyrics_div.get_text(separator='\n').strip()
                            lyrics = re.sub(r'\n\s*\n', '\n\n', lyrics)
                            return lyrics
                    
                    # Fallback: look for any div containing "lyrics" in class
                    for div in soup.find_all('div', class_=re.compile('lyrics', re.I)):
                        lyrics = div.get_text(separator='\n').strip()
                        if lyrics and len(lyrics) > 50:  # Ensure we have substantial content
                            return re.sub(r'\n\s*\n', '\n\n', lyrics)
                            
        except Exception as e:
            print(f"Lyrics extraction error: {e}")
        
        return None

    async def get_song_info(self, song_url):
        """Improved song info extraction"""
        await self.create_session()
        
        try:
            async with self.session.get(song_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Title extraction with multiple patterns
                    title = None
                    title_patterns = [
                        ('h1', {'class': re.compile(r'SongHeader|song_header')}),
                        ('h1', {'class': 'header_with_cover_art-primary_info-title'}),
                        ('h1', {'class': 'song_title'}),
                        ('h1', None)
                    ]
                    
                    for tag, attrs in title_patterns:
                        title_elem = soup.find(tag, attrs)
                        if title_elem:
                            title = title_elem.get_text().strip()
                            break
                    
                    # Artist extraction
                    artist = None
                    artist_patterns = [
                        ('a', {'class': re.compile(r'HeaderArtist|artist_link')}),
                        ('a', {'href': re.compile(r'/artists/')}),
                        ('span', {'class': 'song_artist'}),
                        ('a', {'class': 'song_artist'})
                    ]
                    
                    for tag, attrs in artist_patterns:
                        artist_elem = soup.find(tag, attrs)
                        if artist_elem:
                            artist = artist_elem.get_text().strip()
                            break
                    
                    # Album extraction
                    album = None
                    album_elem = soup.find('a', href=re.compile(r'/albums/'))
                    if album_elem:
                        album = album_elem.get_text().strip()
                    
                    return {
                        'title': title or "Unknown Title",
                        'artist': artist or "Unknown Artist",
                        'album': album or "Unknown Album",
                        'url': song_url
                    }
                    
        except Exception as e:
            print(f"Song info extraction error: {e}")
        
        return None

    async def get_song_lyrics(self, song_url):
        """Extract lyrics from a Genius song page"""
        await self.create_session()
        
        try:
            async with self.session.get(song_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find lyrics container
                    lyrics_div = soup.find('div', {'data-lyrics-container': 'true'})
                    if not lyrics_div:
                        lyrics_div = soup.find('div', class_=re.compile(r'lyrics|Lyrics'))
                    
                    if lyrics_div:
                        # Clean up the lyrics
                        lyrics = lyrics_div.get_text(separator='\n').strip()
                        # Remove extra whitespace and clean up
                        lyrics = re.sub(r'\n\s*\n', '\n\n', lyrics)
                        return lyrics
                        
        except Exception as e:
            print(f"Lyrics extraction error: {e}")
        
        return None

    async def get_song_info(self, song_url):
        """Extract song information from Genius page"""
        await self.create_session()
        
        try:
            async with self.session.get(song_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract song title
                    title_elem = soup.find('h1', class_=re.compile(r'SongHeader'))
                    if not title_elem:
                        title_elem = soup.find('h1')
                    title = title_elem.get_text().strip() if title_elem else "Unknown Title"
                    
                    # Extract artist
                    artist_elem = soup.find('a', class_=re.compile(r'HeaderArtistAndTracklistdesktop'))
                    if not artist_elem:
                        artist_elem = soup.find('a', href=re.compile(r'/artists/'))
                    artist = artist_elem.get_text().strip() if artist_elem else "Unknown Artist"
                    
                    # Extract album info
                    album_elem = soup.find('a', href=re.compile(r'/albums/'))
                    album = album_elem.get_text().strip() if album_elem else "Unknown Album"
                    
                    return {
                        'title': title,
                        'artist': artist,
                        'album': album,
                        'url': song_url
                    }
                    
        except Exception as e:
            print(f"Song info extraction error: {e}")
        
        return None

# Initialize scraper
scraper = GeniusScraper()

# In-memory playlist storage (in production, use a database)
playlists = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready to serve karaoke!')

@bot.command(name='lyrics')
async def get_lyrics(ctx, *, song_name):
    """Fetch and display song lyrics"""
    if not song_name:
        await ctx.send("Please provide a song name! Usage: `/lyrics <song name>`")
        return
    
    await ctx.send(f"🎵 Searching for lyrics: **{song_name}**...")
    
    try:
        # Search for the song
        song_url = await scraper.search_song(song_name)
        if not song_url:
            await ctx.send(f"❌ Couldn't find lyrics for '{song_name}'. Try a different search term!")
            return
        
        # Get lyrics
        lyrics = await scraper.get_song_lyrics(song_url)
        if not lyrics:
            await ctx.send(f"❌ Found the song but couldn't extract lyrics for '{song_name}'")
            return
        
        # Discord has a 2000 character limit, so we need to split long lyrics
        if len(lyrics) > 1900:
            # Split lyrics into chunks
            chunks = [lyrics[i:i+1900] for i in range(0, len(lyrics), 1900)]
            await ctx.send(f"🎤 **Lyrics for {song_name}:**")
            for i, chunk in enumerate(chunks):
                if i < 3:  # Limit to 3 chunks to avoid spam
                    await ctx.send(f"```\n{chunk}\n```")
                else:
                    await ctx.send("... (lyrics too long, showing first part only)")
                    break
        else:
            await ctx.send(f"🎤 **Lyrics for {song_name}:**\n```\n{lyrics}\n```")
            
    except Exception as e:
        await ctx.send(f"❌ An error occurred while fetching lyrics: {str(e)}")

@bot.command(name='track')
async def get_track_info(ctx, *, song_name):
    """Get detailed track information"""
    if not song_name:
        await ctx.send("Please provide a song or artist name! Usage: `/track <song name>`")
        return
    
    await ctx.send(f"🔍 Searching for track info: **{song_name}**...")
    
    try:
        # Search for the song
        song_url = await scraper.search_song(song_name)
        if not song_url:
            await ctx.send(f"❌ Couldn't find track info for '{song_name}'")
            return
        
        # Get song information
        song_info = await scraper.get_song_info(song_url)
        if not song_info:
            await ctx.send(f"❌ Found the song but couldn't extract info for '{song_name}'")
            return
        
        # Create an embed with the track info
        embed = discord.Embed(title="🎵 Track Information", color=0x1DB954)
        embed.add_field(name="Title", value=song_info['title'], inline=True)
        embed.add_field(name="Artist", value=song_info['artist'], inline=True)
        embed.add_field(name="Album", value=song_info['album'], inline=True)
        embed.add_field(name="Genius Link", value=f"[View on Genius]({song_info['url']})", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ An error occurred while fetching track info: {str(e)}")

@bot.command(name='recommend')
async def recommend_songs(ctx, genre=None):
    """Recommend popular songs by genre"""
    if not genre:
        await ctx.send("Please specify a genre! Usage: `/recommend <genre>`\nExample: `/recommend pop`")
        return
    
    # Simple genre-based recommendations (you can expand this)
    recommendations = {
        'pop': ['Shape of You - Ed Sheeran', 'Blinding Lights - The Weeknd', 'Watermelon Sugar - Harry Styles', 'Levitating - Dua Lipa', 'Good 4 U - Olivia Rodrigo'],
        'rock': ['Bohemian Rhapsody - Queen', 'Sweet Child O Mine - Guns N Roses', 'Hotel California - Eagles', 'Stairway to Heaven - Led Zeppelin', 'Smells Like Teen Spirit - Nirvana'],
        'hip-hop': ['God\'s Plan - Drake', 'HUMBLE. - Kendrick Lamar', 'Sicko Mode - Travis Scott', 'Old Town Road - Lil Nas X', 'Rockstar - Post Malone'],
        'r&b': ['Blinding Lights - The Weeknd', 'Peaches - Justin Bieber', 'Levitating - Dua Lipa', 'Good Days - SZA', 'Leave The Door Open - Bruno Mars'],
        'country': ['The Good Ones - Gabby Barrett', 'More Than My Hometown - Morgan Wallen', 'Heartbreak Hotel - Chris Young', 'Life Changes - Thomas Rhett', 'Star Spangled Banner - Chris Stapleton']
    }
    
    genre_lower = genre.lower()
    if genre_lower in recommendations:
        songs = recommendations[genre_lower]
        embed = discord.Embed(title=f"🎵 {genre.title()} Recommendations", color=0xFF6B6B)
        
        for i, song in enumerate(songs, 1):
            embed.add_field(name=f"{i}.", value=song, inline=False)
        
        embed.set_footer(text="Use /lyrics <song name> to get lyrics for any of these songs!")
        await ctx.send(embed=embed)
    else:
        available_genres = ', '.join(recommendations.keys())
        await ctx.send(f"❌ Genre '{genre}' not available. Try one of: {available_genres}")

@bot.command(name='mood')
async def mood_songs(ctx, *, mood=None):
    """Get songs based on your current mood"""
    if not mood:
        await ctx.send("Tell me your mood! Usage: `/mood <your mood>`\nExample: `/mood happy`, `/mood sad`, `/mood energetic`")
        return
    
    mood_songs = {
        'happy': ['Happy - Pharrell Williams', 'Good as Hell - Lizzo', 'Shake It Off - Taylor Swift', 'Uptown Funk - Bruno Mars', 'Can\'t Stop the Feeling - Justin Timberlake'],
        'sad': ['Someone Like You - Adele', 'Hurt - Johnny Cash', 'Mad World - Gary Jules', 'Black - Pearl Jam', 'Tears in Heaven - Eric Clapton'],
        'energetic': ['Thunder - Imagine Dragons', 'Pump It - Black Eyed Peas', 'Eye of the Tiger - Survivor', 'Don\'t Stop Me Now - Queen', 'Confident - Demi Lovato'],
        'chill': ['Stay - Rihanna', 'Summertime - DJ Jazzy Jeff', 'Sunday Morning - Maroon 5', 'Come Away With Me - Norah Jones', 'Breathe Me - Sia'],
        'romantic': ['Perfect - Ed Sheeran', 'All of Me - John Legend', 'Thinking Out Loud - Ed Sheeran', 'A Thousand Years - Christina Perri', 'Make You Feel My Love - Adele']
    }
    
    mood_lower = mood.lower()
    matching_moods = [m for m in mood_songs.keys() if mood_lower in m or m in mood_lower]
    
    if matching_moods:
        selected_mood = matching_moods[0]
        songs = mood_songs[selected_mood]
        
        embed = discord.Embed(title=f"🎭 Songs for {selected_mood.title()} Mood", color=0x9B59B6)
        
        for i, song in enumerate(songs, 1):
            embed.add_field(name=f"{i}.", value=song, inline=False)
        
        embed.set_footer(text="Use /lyrics <song name> to get lyrics for any of these songs!")
        await ctx.send(embed=embed)
    else:
        available_moods = ', '.join(mood_songs.keys())
        await ctx.send(f"❌ I don't have songs for '{mood}' mood yet. Try one of: {available_moods}")

@bot.command(name='playlist')
async def playlist_command(ctx, action=None, *, song_name=None):
    """Manage shared session playlist"""
    guild_id = ctx.guild.id if ctx.guild else ctx.author.id
    
    if guild_id not in playlists:
        playlists[guild_id] = []
    
    if action == 'add' and song_name:
        playlists[guild_id].append(song_name)
        await ctx.send(f"✅ Added '{song_name}' to the playlist!")
        
    elif action == 'remove' and song_name:
        if song_name in playlists[guild_id]:
            playlists[guild_id].remove(song_name)
            await ctx.send(f"✅ Removed '{song_name}' from the playlist!")
        else:
            await ctx.send(f"❌ '{song_name}' not found in the playlist!")
            
    elif action == 'view' or action is None:
        if playlists[guild_id]:
            embed = discord.Embed(title="🎵 Current Playlist", color=0x3498DB)
            for i, song in enumerate(playlists[guild_id], 1):
                embed.add_field(name=f"{i}.", value=song, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("📭 Playlist is empty! Use `/playlist add <song name>` to add songs.")
            
    elif action == 'clear':
        playlists[guild_id] = []
        await ctx.send("🗑️ Playlist cleared!")
        
    else:
        await ctx.send("Usage: `/playlist [add/remove/view/clear] [song name]`\nExamples:\n`/playlist add Bohemian Rhapsody`\n`/playlist view`\n`/playlist remove Bohemian Rhapsody`")

async def help_command(ctx):
    """Show all available commands"""
    embed = discord.Embed(title="🎤 KaraokeBot Commands", description="Your virtual karaoke companion!", color=0xE74C3C)
    
    embed.add_field(
        name="🎵 /lyrics <song name>", 
        value="Fetch and display song lyrics", 
        inline=False
    )
    embed.add_field(
        name="🔍 /track <song name>", 
        value="Get detailed track information (artist, album, etc.)", 
        inline=False
    )
    embed.add_field(
        name="🎲 /recommend <genre>", 
        value="Get 5 popular songs in a specific genre\nGenres: pop, rock, hip-hop, r&b, country", 
        inline=False
    )
    embed.add_field(
        name="🎭 /mood <your mood>", 
        value="Get songs based on your current mood\nMoods: happy, sad, energetic, chill, romantic", 
        inline=False
    )
    embed.add_field(
        name="❓ /help", 
        value="Show this help message", 
        inline=False
    )
    
    embed.set_footer(text="🎵 Happy singing! 🎵")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found! Use `/help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument! Use `/help` for command usage.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        print(f"Error: {error}")

# Cleanup on shutdown
@bot.event
async def on_disconnect():
    await scraper.close_session()

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
    else:
        bot.run(TOKEN)