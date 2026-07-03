from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

def generate_smart_slug(instance, text_field_value, default_prefix):
    if not text_field_value:
        return f"{default_prefix}-{instance.id or 'new'}"

    slug_result = slugify(text_field_value.strip(), allow_unicode=True)
    return slug_result if slug_result else f"{default_prefix}-{instance.id or 'new'}"


class Artist(models.Model):
    name = models.CharField(max_length=200)
    slug_en = models.SlugField(max_length=200, blank=True)
    search_aliases = models.CharField(max_length=100,  blank=True, default="")  # NEW
    image = models.ImageField(upload_to='artists/', blank=True, null=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug_en:
            self.slug_en = generate_smart_slug(self, self.name, 'artist')
        super().save(*args, **kwargs)

    @property
    def followers_count(self):
        return self.artistfollow_set.count()

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100)
    slug_en = models.SlugField(max_length=100, blank=True)
    search_aliases = models.CharField(max_length=100, blank=True, default="")  # NEW

    def save(self, *args, **kwargs):
        if not self.slug_en:
            self.slug_en = generate_smart_slug(self, self.name, 'genre')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Album(models.Model):
    title = models.CharField(max_length=200)
    slug_en = models.SlugField(max_length=200, blank=True)
    search_aliases = models.CharField(max_length=100, blank=True, default="")  # NEW
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    cover = models.ImageField(upload_to='albums/', blank=True, null=True)
    zip_file = models.FileField(upload_to='albums_zip/', blank=True, null=True)
    release_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug_en:
            self.slug_en = generate_smart_slug(self, self.title, 'album')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.artist.name}"


class Music(models.Model):
    title = models.CharField(max_length=200)
    slug_en = models.SlugField(max_length=200, blank=True)
    search_aliases = models.CharField(max_length=100 ,blank=True, default="")  # NEW
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, null=True, blank=True)
    artists = models.ManyToManyField(Artist, related_name='musics', blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='musics/')
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)
    track_number = models.PositiveIntegerField(null=True, blank=True)
    year = models.CharField(max_length=10, null=True, blank=True)
    lyrics = models.TextField(blank=True, null=True)
    is_vip = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.slug_en:
            self.slug_en = generate_smart_slug(self, self.title, 'music')

        # 👇 تشخیص جدید بودن
        is_new = self.pk is None

        # 👇 اول ذخیره کن
        super().save(*args, **kwargs)

        # 👇 بعد از ذخیره برای تلگرام (امپورت داخل بدنه شرط برای حل مشکل کرش)
        if is_new:
            from music.telegram import send_new_music_to_telegram  # 🟢 اضافه شد
            send_new_music_to_telegram(self)


    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comment_set.count()

    def __str__(self):
        return self.title

class TelegramBotState(models.Model):
    last_update_id = models.BigIntegerField(default=0)

    def __str__(self):
        return f"Last Update: {self.last_update_id}"

class TelegramFile(models.Model):
    file_id = models.CharField(max_length=255, unique=True)
    music = models.OneToOneField(Music, on_delete=models.CASCADE)
    def __str__(self):
        return self.music.title

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    music = models.ForeignKey(Music, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'music')


class Comment(models.Model):
    music = models.ForeignKey(Music, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} - {self.music}'


class ArtistFollow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'artist')


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    musics = models.ManyToManyField(Music, blank=True)

    def __str__(self):
        return self.title


class CommentReport(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.user.username} on comment {self.comment.id}"