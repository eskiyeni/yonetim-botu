import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import json
import time

def json_yükle(dosya) -> dict:
    with open(dosya, "r", encoding="utf-8") as d:
        return json.load(d)

def json_yaz(dosya, veri) -> None:
    with open(dosya, "w", encoding="utf-8") as d:
        json.dump(veri, d, ensure_ascii=False, indent=4)

başlangıç = time.time()
config = json_yükle("config.json")
izinler = discord.Intents.all()
bot = commands.Bot(command_prefix=config["prefix"], intents=izinler, help_command=None)
bot.oto_mesaj = json_yükle("oto_mesaj.json")

def uptime() -> str:
    uptime_seconds = int(time.time() - başlangıç)
    days = uptime_seconds // (24 * 3600)
    hours = (uptime_seconds % (24 * 3600)) // 3600
    minutes = (uptime_seconds % 3600) // 60

    return f"{days} gün, {hours} saat, {minutes} dakika"

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Slash komutları yenilendi!")

    print(f"{bot.user.name} aktif!")

@bot.event
async def on_member_join(member : discord.Member):
    if member.guild.id == config["ana_sunucu"]:
        kanal = await bot.fetch_channel(config["giriş_çıkış"])
        user  = await bot.fetch_user(member.id)
        avatar = user.avatar.url if user.avatar else user.default_avatar.url
        banner = user.banner.url if user.banner else None

        await kanal.send(
            embed=discord.Embed(
                title="Yeni Üye!",
                description=f"{user.mention} aramıza katıldı! Artık sunucumuz {member.guild.member_count} üyeye sahip.",
                color=0x00ff00
            ).set_thumbnail(
                url=avatar
            ).set_image(
                url=banner
            )
        )

@bot.event
async def on_member_remove(member : discord.Member):
    if member.guild.id == config["ana_sunucu"]:
        kanal = await bot.fetch_channel(config["giriş_çıkış"])
        user  = await bot.fetch_user(member.id)
        avatar = user.avatar.url if user.avatar else user.default_avatar.url
        banner = user.banner.url if user.banner else None

        await kanal.send(
            embed=discord.Embed(
                title="Ayrılan Üye!",
                description=f"{user.name} aramızdan ayrıldı! Artık sunucumuz {member.guild.member_count} üyeye sahip.",
                color=0xff0000
            ).set_thumbnail(
                url=avatar
            ).set_image(
                url=banner
            )
        )

@bot.event
async def on_message(message : discord.Message):
    if message.guild:
        gid = str(message.guild.id)
        if gid in bot.oto_mesaj.keys():
            for mesaj in bot.oto_mesaj[gid].keys():
                if mesaj in message.content.lower().split():
                    await message.reply(bot.oto_mesaj[gid][mesaj])

    await bot.process_commands(message)

@bot.command(aliases=["info"])
async def bilgi(ctx : commands.Context):
    avatar = bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url
    await ctx.send(
        embed=discord.Embed(
            title="Bilgi",
            description=f"""
Prefix: {config['prefix']}
Uptime: {uptime()}
Kaynak kodları: {config["github_linki"]}
"""         ,
            color=0xF6F478
        ).set_thumbnail(url=avatar
        ).set_footer(text=bot.user.name)
    )

@bot.command()
async def kanala_katıl(ctx : commands.Context, channel : discord.VoiceChannel = None):
    channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
    if channel:
        if ctx.guild:
            if channel.permissions_for(ctx.author).manage_channels:
                await channel.connect(timeout=99999999999999999)
                embed = discord.Embed(
                    title="KANALA KATILINDI",
                    description=f"Bot {channel.name} kanalına katıldı.",
                    color=0x00FF00
                ).set_footer(text=ctx.guild.name)
            else:
                embed = discord.Embed(
                    title="HATA!",
                    description=f"Bu komutu kullanmak için kanalları yönetme iznine sahip olmanız lazım!",
                    color=0xFF0000
                ).set_footer(text=f"Komut {ctx.author.mention} tarafından kullanıldı!")
        else:
            embed = discord.Embed(
                title="HATA",
                description="Bu komut DM üzerinde kullanılamaz.",
                color=0xFF0000
            )
    else:
        embed = discord.Embed(
            title="HATA",
            description="Bir ses kanalına katılmadınız veya bir ses kanalı belirtmediniz!",
            color=0xFF0000
        )

    await ctx.send(embed=embed)

@bot.tree.command(
    name="bilgi",
    description="Bot hakkında bilgi verir."
)
async def bilgi_slash(interaction : discord.Interaction):
    avatar = bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Bilgi",
            description=f"""
Prefix: {config['prefix']}
Uptime: {uptime()}
Kaynak kodları: {config["github_linki"]}
"""         ,
            color=0xF6F478
        ).set_thumbnail(url=avatar
        ).set_footer(text=bot.user.name)
    )

def oto_mesaj_listesi(guild_id: int):
    gid = str(guild_id)
    if gid in bot.oto_mesaj:
        liste = bot.oto_mesaj[gid]
        metin = ""
        for key, value in liste.items():
            metin += f"`{key}`: {value}\n"
    else:
        metin = "Henüz bir mesaj eklenmedi"
    return metin

class OtoMesajEkle(Modal):
    def __init__(self, mesaj_id: int, view : View):
        super().__init__(title="Oto Mesaj Ekle")
        self.add_item(TextInput(label="Tetikleyici"))
        self.add_item(TextInput(label="Yanıt"))
        self.mesaj_id = mesaj_id
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)
        oto_mesaj = bot.oto_mesaj

        if gid not in oto_mesaj:
            oto_mesaj[gid] = {}

        trigger : str = self.children[0].value
        yanit : str = self.children[1].value

        if trigger.lower() in oto_mesaj[gid]:
            await interaction.response.send_message(
                embed=discord.Embed(title="Hata!", description="Bu tetikleyici zaten mevcut.", color=0xff0000),
                ephemeral=True
            )
            return

        bot.oto_mesaj[gid][trigger.lower()] = yanit
        json_yaz("oto_mesaj.json", bot.oto_mesaj)

        await interaction.response.send_message(
            embed=discord.Embed(title="Mesaj Eklendi!", color=0x00ff00),
            ephemeral=True
        )

        mesaj = await interaction.channel.fetch_message(self.mesaj_id)
        await mesaj.edit(
            embed=discord.Embed(
                title="Oto Mesaj",
                description=oto_mesaj_listesi(interaction.guild.id),
                color=0xf6f478
            ),
            view=self.view
        )

class OtoMesajKaldır(Modal):
    def __init__(self, mesaj_id: int, view : View):
        super().__init__(title="Oto Mesaj Kaldır")
        self.add_item(TextInput(label="Tetikleyici"))
        self.mesaj_id = mesaj_id
        self.view = view

    async def on_submit(self, interaction : discord.Interaction):
        gid = str(interaction.guild.id)
        oto_mesaj = bot.oto_mesaj

        if gid not in oto_mesaj:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Hata!",
                    description="Böyle bir tetikleyici bulunmamaktadır!",
                    color=0xff0000
                )
            )
            return
        
        del bot.oto_mesaj[gid][self.children[0].value.lower()]
        json_yaz("oto_mesaj.json", bot.oto_mesaj)

        await interaction.response.send_message(
            embed=discord.Embed(title="Mesaj Kaldırıldı!", color=0x00ff00),
            ephemeral=True
        )

        mesaj = await interaction.channel.fetch_message(self.mesaj_id)
        await mesaj.edit(
            embed=discord.Embed(
                title="Oto Mesaj",
                description=oto_mesaj_listesi(interaction.guild.id),
                color=0xf6f478
            ),
            view=self.view
        )

@bot.tree.command(name="oto-mesaj", description="Oto mesaj sistemi ile ilgili tüm ayarları yönetir.")
async def oto_mesaj(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("Bu komut sadece sunucularda çalışır.", ephemeral=True)
        return

    view = View()

    ekle_buton = Button(label="Mesaj Ekle", style=discord.ButtonStyle.green)
    kaldır_buton = Button(label="Mesaj Kaldır", style=discord.ButtonStyle.danger)

    async def ekle_callback(interaction: discord.Interaction):
        mesaj_id = interaction.message.id
        if interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_modal(OtoMesajEkle(mesaj_id, view))
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Hata!",
                    description="Bunun için yetkin yok!",
                    color=0xff0000
                ),
                ephemeral=True
            )

    async def kaldır_callback(interaction: discord.Interaction):
        mesaj_id = interaction.message.id
        if interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_modal(OtoMesajKaldır(mesaj_id, view))
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Hata!",
                    description="Bunun için yetkin yok!",
                    color=0xff0000
                ),
                ephemeral=True
            )

    ekle_buton.callback = ekle_callback
    kaldır_buton.callback = kaldır_callback

    view.add_item(ekle_buton)
    view.add_item(kaldır_buton)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="Oto Mesaj",
            description=oto_mesaj_listesi(interaction.guild.id),
            color=0xf6f478
        ),
        view=view,
        ephemeral=False
    )

bot.run(config["token"])