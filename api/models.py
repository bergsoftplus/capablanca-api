import uuid
from django.db.models import Model, IntegerField, CharField, TextField, DateTimeField, BooleanField, UUIDField, ForeignKey, CASCADE
from django.conf import settings


class Player(Model):
    guest = BooleanField(default=True)

    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        null=True,  # guest -> not a registered user
    )
    uuid = UUIDField(default=uuid.uuid4)

    def __str__(self):
        return f'Guest #{uuid}' if guest else user


class Elo(Model):
    """
    https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details
    """

    rating = IntegerField(default=1200)
    k_factor = IntegerField(default=32)
    wins = IntegerField(default=0)
    losses = IntegerField(default=0)
    draws = IntegerField(default=0)
    updated_at = DateTimeField(auto_now=True)

    player = ForeignKey(
        Player,
        on_delete=CASCADE,
        null=True
    )

    def _get_expected_score(self, opponent_rating):
        """
        https://wikimedia.org/api/rest_v1/media/math/render/svg/51346e1c65f857c0025647173ae48ddac904adcb
        """

        return 1 / (1 + 10**((opponent_rating - self.rating) / 400))

    def update_rating(self, score, opponent_rating):
        """
        https://wikimedia.org/api/rest_v1/media/math/render/svg/09a11111b433582eccbb22c740486264549d1129

        Update rating after a single game (i.e score should be either 0, 0.5 or 1)
        """

        expected_score = self._get_expected_score(opponent_rating)
        self.rating = round(self.rating + self.k_factor *
                            (score - expected_score))
        self.save()


class Result(Model):
    SCHEDULED = 'Scheduled'
    POSTPONED = 'Postponed'
    FINISHED_NO_MOVES = 'Finished (no moves)'
    IN_PROGRESS = 'In progress'
    ADJOURNED = 'Adjourned'
    FINISHED_BASIC_RULES = 'Finished (basic rules)'
    FINISHED_CLOCK = 'Finished (clock)'
    DRAW = 'Draw'
    FINISHED_BREACH = 'Finished (breach)'
    FINISHED_COMPLIANCE = 'Finished (compliance)'
    TBD = 'TBD'
    ABANDONED = 'Abandoned'
    UNKNOWN = 'Unknown'

    RESULT_CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (POSTPONED, 'Postponed'),
        (FINISHED_NO_MOVES, 'Finished without any moves played'),
        (IN_PROGRESS, 'In progress'),
        (ADJOURNED, 'Adjourned'),
        (FINISHED_BASIC_RULES, 'Finished according to the Basic Rules of Play'),
        (FINISHED_CLOCK, 'Finished by the clock'),
        (DRAW, 'Draw'),
        (FINISHED_BREACH, 'Finished because of a breach of rules of one player'),
        (FINISHED_COMPLIANCE,
         'Finished because both players persistently refuse to comply with the laws of chess'),
        (TBD, 'To be decided'),
        (ABANDONED, 'Abandoned'),
        (UNKNOWN, 'Unknown'),
    ]

    description = TextField(
        choices=RESULT_CHOICES,
        default=IN_PROGRESS
    )

    def __str__(self):
        return self.description


class Board(Model):
    layout = TextField(
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return self.layout


class Piece(Model):
    BLACK_PAWN = "P"
    BLACK_KNIGHT = "N"
    BLACK_BISHOP = "B"
    BLACK_ROOK = "R"
    BLACK_QUEEN = "Q"
    BLACK_KING = "K"
    WHITE_PAWN = "p"
    WHITE_KNIGHT = "n"
    WHITE_BISHOP = "b"
    WHITE_ROOK = "r"
    WHITE_QUEEN = "q"
    WHITE_KING = "k"

    PIECE_CHOICES = [
        (BLACK_PAWN, "Black pawn"),
        (BLACK_KNIGHT, "Black knight"),
        (BLACK_BISHOP, "Black bishop"),
        (BLACK_ROOK, "Black rook"),
        (BLACK_QUEEN, "Black queen"),
        (BLACK_KING, "Black king"),
        (WHITE_PAWN, "White pawn"),
        (WHITE_KNIGHT, "White knight"),
        (WHITE_BISHOP, "White bishop"),
        (WHITE_ROOK, "White rook"),
        (WHITE_QUEEN, "White queen"),
        (WHITE_KING, "White king"),
    ]

    piece_type = CharField(
        max_length=1,
        choices=PIECE_CHOICES,
    )

    captured = BooleanField(default=False)
    board = ForeignKey(
        Board,
        on_delete=CASCADE,
    )

    def __str__(self):
        return self.piece_type


class Game(Model):
    uuid = UUIDField(default=uuid.uuid4, primary_key=True)
    whites_player = ForeignKey(
        Player,
        on_delete=CASCADE,
        related_name='whites_player',
    )
    blacks_player = ForeignKey(
        Player,
        on_delete=CASCADE,
        related_name='blacks_player',
    )
    start_timestamp = DateTimeField(auto_now_add=True)
    end_timestamp = DateTimeField(null=True)
    result = ForeignKey(
        Result,
        on_delete=CASCADE,
    )
    board = ForeignKey(
        Board,
        on_delete=CASCADE,
    )


class Move(Model):
    timestamp = DateTimeField(auto_now_add=True)
    piece = ForeignKey(
        Piece,
        on_delete=CASCADE,
    )
    from_square = TextField()
    to_square = TextField()

    def __str__(self):
        return f'{from_square}{to_square}'


class Position(Model):
    piece_file = CharField(max_length=1)
    piece_rank = CharField(max_length=1)
    timestamp = DateTimeField(auto_now_add=True)
    uuid = UUIDField(default=uuid.uuid4)
    piece = ForeignKey(
        Piece,
        on_delete=CASCADE,
    )

    def __str__(self):
        return f'{piece_file}{piece_rank}'


class Claim(Model):
    THREEFOLD_REPETITION = 'tr'
    FIFTY_MOVES = 'ft'
    DRAW = 'd'

    CLAIM_CHOICES = [
        (THREEFOLD_REPETITION, 'Threefold repetition'),
        (FIFTY_MOVES, 'Fifty moves'),
        (DRAW, 'Draw'),
    ]

    claim_type = CharField(
        max_length=2,
        choices=CLAIM_CHOICES,
    )

    def __str__(self):
        return self.claim_type


class ClaimItem(Model):
    player = ForeignKey(
        Player,
        on_delete=CASCADE,
    )
    timestamp = DateTimeField(auto_now_add=True)
    claim = ForeignKey(
        Claim,
        on_delete=CASCADE,
    )
