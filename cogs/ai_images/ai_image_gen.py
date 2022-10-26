import discord
from discord import Interaction, app_commands
from discord.ext import commands, tasks
from discord.app_commands import Choice
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import NoSuchElementException
import os
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
import asyncio
import time
from functools import wraps, partial
import requests
from config import GLOBAL_SYNC

commandExamples = dict()
commandExamples = {
    "dalle" : "/ai_images dalle <image prompt> OPTIONAL<artist> OPTIONAL<style>",
    "deepai" : "/ai_images deepai <image prompt>",
    "dalle2" : "/ai_images dalle2 <image prompt> OPTIONAL<artist> OPTIONAL<style>",
    "dalle2" : "/ai_images dalle2_account_updater",
    "dalle2" : "/ai_images dalle2_account_checker",
    "help" : "/ai_images help"
}

async def get_msg_content(self, dm: discord.Message, msg_response: discord.Message) -> None:
    if dm.channel.id == msg_response.channel.id:
        channel = self.bot.get_channel(dm.channel.id)
        if channel is None:
            return print("Could not find channel")

        content = await channel.fetch_message(msg_response.id)
    else:
        print("Not sent in same channel")
    
    return content

class AIImageGen(commands.GroupCog, name="ai_images"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.dalle_id_list = []
        self.dalle2_id_list = []
        self.cwd = os.getcwd()
        self.credentials = dict()
        super().__init__()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"AI Image Generation cog is now ready. Synced Globally: {GLOBAL_SYNC}")
    
    #
    #   DALLE Mini
    #
    @app_commands.command(name="dalle", description="Generate images from a prompt using DALL·E Mini AI")
    @app_commands.choices(artist=[
        Choice(name="Leonardo da Vinci", value="Leonardo da Vinci"), 
        Choice(name="Michelangelo", value="Michelangelo"), 
        Choice(name="Rembrandt", value="Rembrandt"),
        Choice(name="Vermeer", value="Vermeer"),
        Choice(name="Jean-Antoine Watteau", value="Jean-Antoine Watteau"),
        Choice(name="Eugene Delacroix", value="Eugene Delacroix"),
        Choice(name="Claude Monet", value="Claude Monet"),
        Choice(name="Georges Seurat", value="Georges Seurat"),
        Choice(name="Vincent van Gogh", value="Vincent van Gogh"),
        Choice(name="Edvard Munch", value="Edvard Munch"),
        Choice(name="Egon Schiele", value="Egon Schiele"),
        Choice(name="Gustav Klimt", value="Gustav Klimt"),
        Choice(name="Pablo Picasso", value="Pablo Picasso"),
        Choice(name="Henri Matisse", value="Henri Matisse"),
        Choice(name="Rene Magritte", value="Rene Magritte"),
        Choice(name="Salvador Dalí", value="Salvador Dalí"),
        Choice(name="Georgia O'Keeffe", value="Georgia O'Keeffe"),
        Choice(name="Edward Hopper", value="Edward Hopper"),
        Choice(name="Yoji Shinkawa", value="Yoji Shinkawa"),
        Choice(name="Toshi Yoshida", value="Toshi Yoshida"),
        Choice(name="Ivan Bilibin", value="Ivan Bilibin"),
        Choice(name="Kuniyoshi", value="Kuniyoshi"),
        ])
    @app_commands.choices(style=[
        Choice(name="Abstract Expressionism", value="Abstract Expressionism"),
        Choice(name="Art Deco", value="Art Deco"),
        Choice(name="Baroque", value="Baroque"),
        Choice(name="Bauhaus", value="Bauhaus"),
        Choice(name="Classicism", value="Classicism"),
        Choice(name="Color Field Painting", value="Color Field Painting"),
        Choice(name="Conceptual Art", value="Conceptual Art"),
        Choice(name="Constructivism", value="Constructivism"),
        Choice(name="Cubism", value="Cubism"),
        Choice(name="Digital Art", value="Digital Art"),
        Choice(name="Expressionism", value="Expressionism"),
        Choice(name="Fauvism", value="Fauvism"),
        Choice(name="Futurism", value="Futurism"),
        Choice(name="Harlem Renaissance", value="Harlem Renaissance"),
        Choice(name="Impressionism", value="Impressionism"),
        Choice(name="Minimalism", value="Minimalism"),
        Choice(name="Neo-Impressionism", value="Neo-Impressionism"),
        Choice(name="Neoclassicism", value="Neoclassicism"),
        Choice(name="Neon Art", value="Neon Art"),
        Choice(name="Street Art", value="Street Art"),
        Choice(name="Surrealism", value="Surrealism"),
        ])
    async def dalle_command(self, interaction: discord.Interaction, prompt: str, artist: Optional[str] = None, style: Optional[str] = None) -> None:
        if interaction.user.id in self.dalle_id_list:
            embed = discord.Embed(title="Please wait for your current DALL-E image to complete", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            if artist is not None:
                prompt += f", by {artist}"
            if style is not None:
                prompt += f", in the style of {style}"
            #self.dalle_id_list.append(interaction.user.id)
            await self.execute_dalle(interaction, prompt)
    
    async def execute_dalle(self, interaction: discord.Interaction, prompt: str):
        loading_emoji = self.bot.get_emoji(997263536076107827)

        #cloudinary account details for uploading images
        cloudinary.config( 
            cloud_name = os.environ["CLOUD_NAME"], 
            api_key = os.environ["API_KEY"], 
            api_secret = os.environ["API_SECRET"] 
        )

        # Send embeded message to discord stating the image generation has started
        embed = discord.Embed(title=f"Generating DALL·E Mini Image now! {loading_emoji}", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_thumbnail(url="https://www.craiyon.com/_app/immutable/assets/craiyon_logo-9927047c.png")
        embed.set_footer(text="Please allow for up to 3 minutes.")
        await interaction.response.defer()
        # Get last sent message id so we can edit/delete when generation complete
        msg = await interaction.followup.send(embed=embed)

        # Generate unique image name based on author of command
        image_name = f"Dalle_Image_{interaction.user.id}_{str(uuid.uuid4().hex)}.png"

        await self.dalle_wait_for_loading(prompt)

        # Find downloaded image in download folder, change name, upload to cloud website while saving it's URL and removing from downloads
        for i in  os.listdir(self.cwd):
            if i.startswith("craiyon_"):
                os.rename(f"{self.cwd}/{i}", f"{self.cwd}/{image_name}")
                image_url = cloudinary.uploader.upload_image(f"{self.cwd}/{image_name}", folder="Dalle Images/", use_filename = True).url
                os.remove(f"{self.cwd}/{image_name}")

        
        # Send embeded discord message with the generated IMG's URL 
        embed = discord.Embed(title=f"{interaction.user.name}'s DALL·E Mini Search Finished!", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_footer(text="Website Link: https://www.craiyon.com")
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)
        #self.dalle_id_list.remove(interaction.user.id)
        embed = discord.Embed(title="Images Generated", color=discord.Color.from_rgb(255, 255, 255))
        await msg.edit(embed=embed)

    # Wrap sync function in async decorator to run concurrently
    def wrap(func):
        @wraps(func)
        async def run(*args, loop=None, executor=None, **kwargs):
            if loop is None:
                loop = asyncio.get_event_loop()
            pfunc = partial(func, *args, **kwargs)
            return await loop.run_in_executor(executor, pfunc)
        return run

    # Use decorator to wrap long-running blocking code
    @wrap
    def dalle_wait_for_loading(self, prompt):
        #Dalle Information
        LOADING_ELEMENT = "//*[contains(text(), 'This should not take long (up to 2 minutes)...')]"
        SCREENSHOT_BUTTON = "//*[contains(text(), 'Screenshot')]"
        RUN_BUTTON = '//*[@id="app"]/div/div/div[1]/button'
        POPUP_REJECT_ALL = "/html/body/div[1]/div/div/div/div[2]/div/button[2]"
        VIDEO_POPUP_EXIT = "//*[@id='av-close-btn']"

        #apply options to browser. Not currently used as headless causes program to crash
        #standard options work fine but window pops up when command runs
        chrome_options = webdriver.ChromeOptions()
        prefs = {'download.default_directory' : f"{self.cwd}"}
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

        #navigate to dalle page
        driver.get("https://www.craiyon.com/")

        try:
            element = WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, POPUP_REJECT_ALL)))
            print("Popup found")
            driver.execute_script("arguments[0].click();", element)
            print("Popup rejected")
        except TimeoutException:
            print("Couldnt find popup menu in time")
        except ElementClickInterceptedException:
            print("Could not click reject on popup menu")
        except ElementNotInteractableException:
            print("Found element but could not click")
        
        #find website input box and type in prompt
        driver.find_element(By.ID, "prompt").send_keys(prompt)
        print("Prompt entered")
        #find website submit button and click
        element = driver.find_element(By.XPATH, RUN_BUTTON)
        print("Found run button")
        driver.execute_script("arguments[0].click();", element)
        print("Clicked run")

        # Loading element precense is checked to ensure generation has started.
        try:
            WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, LOADING_ELEMENT)))
            print("Loading element found.")

            # When loading element disappears we know generation has completed
            WebDriverWait(driver, 180).until_not(ec.presence_of_element_located((By.XPATH, LOADING_ELEMENT)))
            print("Loading stopped.")
        except TimeoutException:
            return print("Could not find loading element in time.")
        except ElementClickInterceptedException:
            return print("Element Click Intercepted Exception Raised.")
        except UnexpectedAlertPresentException:
            return print("Unexpected Alart Present")

        try:
            element = WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, VIDEO_POPUP_EXIT)))
            print("Video popup found element found.")
            driver.execute_script("arguments[0].click();", element)
            print("Video popup closed")
        except TimeoutException:
            print("could not find video popup")
        except ElementClickInterceptedException:
            print("Element Click Intercepted Exception Raised. POPUP VIDEO")
        except UnexpectedAlertPresentException:
            print("Unexpected Alert Present")

        try:
            element = WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, SCREENSHOT_BUTTON)))
            driver.execute_script("arguments[0].click();", element)
            time.sleep(3)
            print("Screenshot taken")
        except TimeoutException:
            print("could not find screenshot button")
        except ElementClickInterceptedException:
            print("Element Click Intercepted Exception Raised. POPUP VIDEO")
        except UnexpectedAlertPresentException:
            print("Unexpected Alert Present")

        # close driver
        driver.close()
        print("Driver closed. DALL·E Mini img generation complete.")

    #
    #   DEEP AI
    #
    @app_commands.command(name="deepai", description="Generate an AI image from text prompt with DeepAI")
    async def deepai(self, interaction: discord.Interaction, prompt: str) -> None:
        if interaction.user.id in self.dalle_id_list:
            embed = discord.Embed(title="Please wait for your current DALL-E image to complete", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)
            
        self.dalle_id_list.append(interaction.user.id)

        loading_emoji = self.bot.get_emoji(997263536076107827)
        
        await interaction.response.defer()
        embed = discord.Embed(title=f"Generating DeepAI Image now! {loading_emoji}", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_thumbnail(url="https://6lli539m39y3hpkelqsm3c2fg-wpengine.netdna-ssl.com/wp-content/uploads/2020/10/DeepAi-Logo.png")
        embed.set_footer(text="Please allow for up to 2 minutes.")
        # Get last sent message id so we can edit/delete when generation complete
        msg = await interaction.followup.send(embed=embed)

        try:
            r = requests.post("https://api.deepai.org/api/text2img",
                data={'text': prompt},
                headers={'api-key': 'cee54a56-e8e8-4dc4-86f4-cb7772582372'})

            content = r.json()
            print(content)
            image_url = content["output_url"]
        except KeyError:
            return await interaction.followup.send("Could not complete request, please try again.")


        embed = discord.Embed(title=f"{interaction.user.name}'s DeepAI Search Finished!", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_footer(text="Website Link: https://www.craiyon.com")
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)
        self.dalle_id_list.remove(interaction.user.id)
        embed = discord.Embed(title="Images Generated", color=discord.Color.from_rgb(255, 255, 255))
        await msg.edit(embed=embed)
    
    #
    #   DALLE 2
    #
    @app_commands.command(name="dalle2_account_updater", description="Update your dalle 2 account information")
    async def account_updater(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in self.credentials:
            await interaction.response.defer()
            embed = discord.Embed(title=f"No DALL·E 2 information found.\n\nWould you like to add your account information now?", color=discord.Color.from_rgb(255, 0, 0))
            message = await interaction.followup.send(embed=embed, ephemeral=True)
            await message.add_reaction('✔️')
            await message.add_reaction('❌')
            
            def check(response, user):
                return user == interaction.user and response.emoji in ['✔️', '❌']
            
            try:
                reaction = await self.bot.wait_for('reaction_add', timeout=5.0, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(title=f"{interaction.user.name} Didn't react in time",
                                color=discord.Color.from_rgb(255, 0, 0))
                return await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                if reaction[0].emoji == '✔️':
                    embed = discord.Embed(title="Please check your DM's to update your DALL·E 2 account information", color=discord.Color.from_rgb(255, 255, 255))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    await self.register_new(interaction)
        else:
            embed = discord.Embed(title=f"Please check your DM's to update your account information", color=discord.Color.from_rgb(255, 255, 255))
            await self.update_info(interaction)

    @app_commands.command(name="dalle2_account_checker", description="Check if Brian has your DALL·E 2 account information")
    async def account_checker(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in self.credentials:
            await interaction.response.defer()
            embed = discord.Embed(title=f"No Dalle 2 information found.\n\nWould you like to add your account information now?", color=discord.Color.from_rgb(255, 0, 0))
            message = await interaction.followup.send(embed=embed, ephemeral=True)
            await message.add_reaction('✔️')
            await message.add_reaction('❌')
            
            def check(response, user):
                return user == interaction.user and response.emoji in ['✔️', '❌']
            
            try:
                reaction = await self.bot.wait_for('reaction_add', timeout=5.0, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(title=f"{interaction.user.name} Didn't react in time",
                                color=discord.Color.from_rgb(255, 0, 0))
                return await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                if reaction[0].emoji == '✔️':
                    embed = discord.Embed(title="Please check your DM's to add your Dalle 2 account information", color=discord.Color.from_rgb(255, 255, 255))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return await self.register_new(interaction)
        else:
            embed = discord.Embed(title=f"We have your Dalle 2 information stored, {interaction.user.name}!\nemail: {self.credentials[interaction.user.id][0]}\npassword: {self.credentials[interaction.user.id][1]}", color=discord.Color.from_rgb(0, 255, 0))
            return await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="dalle2", description="Create AI art with DALL·E 2")
    @app_commands.choices(artist=[
    Choice(name="Leonardo da Vinci", value="Leonardo da Vinci"), 
    Choice(name="Michelangelo", value="Michelangelo"), 
    Choice(name="Rembrandt", value="Rembrandt"),
    Choice(name="Vermeer", value="Vermeer"),
    Choice(name="Jean-Antoine Watteau", value="Jean-Antoine Watteau"),
    Choice(name="Eugene Delacroix", value="Eugene Delacroix"),
    Choice(name="Claude Monet", value="Claude Monet"),
    Choice(name="Georges Seurat", value="Georges Seurat"),
    Choice(name="Vincent van Gogh", value="Vincent van Gogh"),
    Choice(name="Edvard Munch", value="Edvard Munch"),
    Choice(name="Egon Schiele", value="Egon Schiele"),
    Choice(name="Gustav Klimt", value="Gustav Klimt"),
    Choice(name="Pablo Picasso", value="Pablo Picasso"),
    Choice(name="Henri Matisse", value="Henri Matisse"),
    Choice(name="Rene Magritte", value="Rene Magritte"),
    Choice(name="Salvador Dalí", value="Salvador Dalí"),
    Choice(name="Georgia O'Keeffe", value="Georgia O'Keeffe"),
    Choice(name="Edward Hopper", value="Edward Hopper"),
    Choice(name="Yoji Shinkawa", value="Yoji Shinkawa"),
    Choice(name="Toshi Yoshida", value="Toshi Yoshida"),
    Choice(name="Ivan Bilibin", value="Ivan Bilibin"),
    Choice(name="Kuniyoshi", value="Kuniyoshi"),
    ])
    @app_commands.choices(style=[
    Choice(name="Abstract Expressionism", value="Abstract Expressionism"),
    Choice(name="Art Deco", value="Art Deco"),
    Choice(name="Baroque", value="Baroque"),
    Choice(name="Bauhaus", value="Bauhaus"),
    Choice(name="Classicism", value="Classicism"),
    Choice(name="Color Field Painting", value="Color Field Painting"),
    Choice(name="Conceptual Art", value="Conceptual Art"),
    Choice(name="Constructivism", value="Constructivism"),
    Choice(name="Cubism", value="Cubism"),
    Choice(name="Digital Art", value="Digital Art"),
    Choice(name="Expressionism", value="Expressionism"),
    Choice(name="Fauvism", value="Fauvism"),
    Choice(name="Futurism", value="Futurism"),
    Choice(name="Harlem Renaissance", value="Harlem Renaissance"),
    Choice(name="Impressionism", value="Impressionism"),
    Choice(name="Minimalism", value="Minimalism"),
    Choice(name="Neo-Impressionism", value="Neo-Impressionism"),
    Choice(name="Neoclassicism", value="Neoclassicism"),
    Choice(name="Neon Art", value="Neon Art"),
    Choice(name="Street Art", value="Street Art"),
    Choice(name="Surrealism", value="Surrealism"),
    ])
    async def dalle2_command(self, interaction: discord.Interaction, prompt: str, artist: Optional[str] = None, style: Optional[str] = None) -> None:
        if interaction.user.id not in self.credentials:
            embed = discord.Embed(title=f"No DALL·E 2 information registered. Please check your DM's to set up your account", color=discord.Color.from_rgb(255, 0, 0))
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return await self.register_new(interaction)
        
        if interaction.user.id in self.dalle2_id_list:
            embed = discord.Embed(title="Please wait for your current DALL·E 2 image to complete", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            if artist is not None:
                prompt += f", by {artist}"
            if style is not None:
                prompt += f", in the style of {style}"
            await self.execute_dalle2(interaction, prompt)
    
    async def execute_dalle2(self, interaction: discord.Interaction, prompt: str):
        loading_emoji = self.bot.get_emoji(997263536076107827)

        # Send embeded message to discord stating the image generation has started
        embed = discord.Embed(title=f"Generating DALL·E 2 Image now! {loading_emoji}", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_thumbnail(url="https://openai.com/content/images/2022/05/twitter-1.png")
        embed.set_footer(text="Please allow for up to 90 seconds.")
        await interaction.response.defer()
        # Get last sent message id so we can edit/delete when generation complete
        msg = await interaction.followup.send(embed=embed)

        images = await self.dalle2_wait_for_loading(interaction, prompt, self.credentials[interaction.user.id][0], self.credentials[interaction.user.id][1], interaction.user.id)

        await msg.edit(embed=embed)
        if images is None:
            embed = discord.Embed(title=f"Error Encountered!", description="Sorry! Brian encountered an error while fetching your images, please try again", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.followup.send(embed=embed, ephemeral=True)
        if images is "Content Policy Warning":
            embed = discord.Embed(title=f"Error Encountered!", description="Sorry! Your prompt breaks some of Dalle 2's content policy rules, please try a different prompt", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            # Send embeded discord message with the generated IMG's URL 
            embed = discord.Embed(title=f"{interaction.user.name}'s DALL·E 2 Search Finished!", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
            embed.set_footer(text="Website Link: https://openai.com/dall-e-2/")
            await interaction.followup.send(embed=embed)
            embed = discord.Embed(title="Images Generated", color=discord.Color.from_rgb(255, 255, 255))
            for image in images:
                await interaction.followup.send(image)

    # Use decorator to wrap long-running blocking code
    @wrap
    def dalle2_wait_for_loading(self, interaction: discord.Interaction, prompt, email, password, user_id):
        #Dalle2 Information
        LOGIN_BUTTON = "//*[contains(text(), 'Log in')]"
        LOGIN_CONTINUE_BUTTON = "/html/body/main/section/div/div/div/form/div[2]/button"
        PROMPT_BOX = '//*[@id="root"]/div[1]/div/div/div/div/div[2]/form/input'
        GENERATE_BTN = '//*[@id="root"]/div[1]/div/div/div/div/div[2]/form/button/span/span'

        LOADING_BAR = '//*[@id="root"]/div[1]/div/div/div[1]/div/div/div/div[2]/div/div[1]'
        CONTENT_POLICY_WARNING = "//*[contains(text(), 'It looks like this request may not follow our')]"

        IMAGE_1_SRC = '/html/body/div[1]/div[1]/div/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div/div/a/div/img'
        IMAGE_2_SRC = '/html/body/div[1]/div[1]/div/div/div[1]/div/div/div/div[2]/div[1]/div[2]/div/div/a/div/img'
        IMAGE_3_SRC = '/html/body/div[1]/div[1]/div/div/div[1]/div/div/div/div[2]/div[1]/div[3]/div/div/a/div/img'
        IMAGE_4_SRC = '/html/body/div[1]/div[1]/div/div/div[1]/div/div/div/div[2]/div[1]/div[4]/div/div/a/div/img'

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("excludeSwitches", ['enable-logging'])
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

        driver.get("https://labs.openai.com/auth/login")

        #locate and press login
        element = WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.XPATH, LOGIN_BUTTON)))
        driver.execute_script("arguments[0].click();", element)
        print("Login Clicked")
        
        try:
            #Log in information
            #username
            WebDriverWait(driver, 5).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="username"]')))
            element = driver.find_element(By.XPATH, '//*[@id="username"]')
            element.click()
            element.clear()
            element.send_keys(email)
            #find website continue button and click
            element = driver.find_element(By.XPATH, LOGIN_CONTINUE_BUTTON)
            driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            driver.close()
            print(e)

        try:
            #password
            WebDriverWait(driver, 5).until(ec.element_to_be_clickable((By.XPATH, '//*[@id="password"]')))
            element = driver.find_element(By.XPATH, '//*[@id="password"]')
            element.click()
            element.clear()
            element.send_keys(password)
            #find website continue button and click
            element = driver.find_element(By.XPATH, LOGIN_CONTINUE_BUTTON)
            driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            driver.close()
            print(e)

        WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, PROMPT_BOX)))
        driver.find_element(By.XPATH, PROMPT_BOX).send_keys(prompt)
        print("Prompt entered")

        WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, GENERATE_BTN)))
        element = driver.find_element(By.XPATH, GENERATE_BTN)
        driver.execute_script("arguments[0].click();", element)

        time.sleep(3)

        try:
            warning_check = driver.find_element(By.XPATH, CONTENT_POLICY_WARNING)
            if warning_check is not None:
                result = "Content Policy Warning"
        except NoSuchElementException:
            #Add user ID to list when generation starts to stop multiple generation requests
            self.dalle2_id_list.append(user_id)

            try:
                print("Content policy not broken")
                WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, LOADING_BAR)))
                print("Loading element found.")
                # When images pop up we know generation has completed
                WebDriverWait(driver, 180).until(ec.presence_of_element_located((By.XPATH, IMAGE_1_SRC)))
                print("Loading stopped. Pictures found")

                WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, IMAGE_1_SRC)))
                time.sleep(3)
                image1 = driver.find_element(By.XPATH, IMAGE_1_SRC).get_attribute("src")

                WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, IMAGE_2_SRC)))
                time.sleep(3)
                image2 = driver.find_element(By.XPATH, IMAGE_2_SRC).get_attribute("src")

                WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, IMAGE_3_SRC)))
                time.sleep(3)
                image3 = driver.find_element(By.XPATH, IMAGE_3_SRC).get_attribute("src")

                WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, IMAGE_4_SRC)))
                time.sleep(3)
                image4 = driver.find_element(By.XPATH, IMAGE_4_SRC).get_attribute("src")

            except TimeoutException:
                self.dalle2_id_list.remove(user_id)
                return print("could not find Image")
            except ElementClickInterceptedException:
                self.dalle2_id_list.remove(user_id)
                return print("ElementClickInterceptedException")
            except UnexpectedAlertPresentException:
                self.dalle2_id_list.remove(user_id)
                return print("Unexpected Alert Present")
        
            finally:
                # close driver
                driver.close()
                result = [image1, image2, image3, image4]
                self.dalle2_id_list.remove(user_id)
                
        return result

    async def register_new(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="Do you have a DALL·E 2 account registered?", color=discord.Color.from_rgb(255, 255, 255))
        dm = await interaction.user.send(embed=embed)
        await dm.add_reaction('✔️')
        await dm.add_reaction('❌')

        def check(response, user):
            return user == interaction.user and response.emoji in ['✔️', '❌']
        
        try:
            reaction = await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Unfortunately you didn't respond in time. Please run the command to try again", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.user.send(embed=embed)
        else:
            if reaction[0].emoji == '✔️':
                embed = discord.Embed(title="Perfect! Please type your DALL·E 2 email...", color=discord.Color.from_rgb(255, 255, 255))
                dm = await interaction.user.send(embed=embed)

                try:
                    email_response = await self.bot.wait_for("message", timeout=30.0)
                except asyncio.TimeoutError:
                    embed = discord.Embed(title="Unfortunately you didn't respond in time. Please run the command to try again", color=discord.Color.from_rgb(255, 0, 0))
                    return await interaction.user.send(embed=embed)


                if(email_response.author.id is interaction.user.id):
                    email = await get_msg_content(self, dm, email_response)
                else:
                    embed = discord.Embed(title="Sorry I run into an error. Please try again.", color=discord.Color.from_rgb(255, 0, 0))
                    return await interaction.user.send(embed=embed)
                
                embed = discord.Embed(title="Please type your DALL·E 2 password...", color=discord.Color.from_rgb(255, 255, 255))
                dm = await interaction.user.send(embed=embed)

                try:
                    password_response = await self.bot.wait_for("message", timeout=30.0)
                except asyncio.TimeoutError:
                    embed = discord.Embed(title="Unfortunately you didn't respond in time. Please run the command to try again", color=discord.Color.from_rgb(255, 0, 0))
                    return await interaction.user.send(embed=embed)

                if(password_response.author.id is interaction.user.id):
                    password = await get_msg_content(self, dm, password_response)
                else:
                    embed = discord.Embed(title="Sorry I run into an error. Please try again.", color=discord.Color.from_rgb(255, 0, 0))
                    return await interaction.user.send(embed=embed)

                info = [email.content, password.content]

                self.credentials[interaction.user.id] = info

                embed = discord.Embed(title="Credentials Stored! You should now be able to use the DALL·E 2 command", color=discord.Color.from_rgb(0, 255, 0))
                return await interaction.user.send(embed=embed)
            if reaction[0].emoji == '❌':
                embed = discord.Embed(title="Create DALL·E 2 Account", description="Please visit [DALL·E 2's website](https://openai.com/dall-e-2/) to create an acccount", color=discord.Color.from_rgb(255, 255, 255))
                return await interaction.user.send(embed=embed)

    async def update_info(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="Please type your DALL·E 2 email...", color=discord.Color.from_rgb(255, 255, 255))
        dm = await interaction.user.send(embed=embed)
        try:
            email_response = await self.bot.wait_for("message", timeout=30.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Unfortunately you didn't respond in time. Please run the command to try again", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.user.send(embed=embed)

        if(email_response.author.id is interaction.user.id):
            email = await get_msg_content(self, dm, email_response)
        else:
            embed = discord.Embed(title="Sorry I run into an error. Please try again.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.user.send(embed=embed)
        
        embed = discord.Embed(title="Please type your DALL·E 2 password...", color=discord.Color.from_rgb(255, 255, 255))
        dm = await interaction.user.send(embed=embed)
        try:
            password_response = await self.bot.wait_for("message", timeout=30.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Unfortunately you didn't respond in time. Please run the command to try again", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.user.send(embed=embed)

        if(password_response.author.id is interaction.user.id):
            password = await get_msg_content(self, dm, password_response)
        else:
            embed = discord.Embed(title="Sorry I run into an error. Please try again.", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.user.send(embed=embed)

        info = [email.content, password.content]
        
        embed = discord.Embed(title="Are you sure you want to update your account information with these?", color=discord.Color.from_rgb(255, 255, 255))
        dm = await interaction.user.send(embed=embed)

        await dm.add_reaction('✔️')
        await dm.add_reaction('❌')
        
        def check(response, user):
            return user == interaction.user and response.emoji in ['✔️', '❌']
        
        try:
            reaction = await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Sorry! You didn't react in time. Please try again", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.user.send(embed=embed)
        else:
            if reaction[0].emoji == '✔️':
                self.credentials.pop(interaction.user.id)
                self.credentials[interaction.user.id] = info
                embed = discord.Embed(title="Account information successfully updated!")
                return await interaction.user.send(embed=embed)
    
    @app_commands.command(name="help", description="Get help with Bot Brians AI Image commands")
    async def aiimage_help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="AI Image Generation Commands", description="List of all Bot Brians AI Image generation commands with examples", color=discord.Color.from_rgb(0, 255, 0))

        cog = self.bot.get_cog("ai_images")
        group = cog.app_command
        for command in group.commands:
            embed.add_field(name=command.name, value=f"`{command.description}`\n`{commandExamples.get(command.name)}`", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    if GLOBAL_SYNC:
        # Global Sync
        await bot.add_cog(AIImageGen(bot))
    else:
        # Private Sync
        await bot.add_cog(AIImageGen(bot), guilds=[discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"])])