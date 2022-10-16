import re
import sys
from argparse import ArgumentParser
from typing import Iterable, Tuple, List

class Racer:
    def __init__(self, line: str):
        self.description = Racer.__remove_tokens(line)
        self.ability_score = Racer.__parse_ability_score(self.description)

    def speed(self) -> int:
        return self.ability_score[0]

    def attack(self) -> int:
        return self.ability_score[1]

    def defence(self) -> int:
        return self.ability_score[2]

    @staticmethod
    def __remove_tokens(line: str) -> str:
        line = line.strip("+").strip("-")
        return re.sub(r'\[.+\]', "", line)

    @staticmethod
    def __parse_ability_score(description: str) -> Tuple[int]:
        match = Racer.__match_ability_score(description)
        assert match, "Description '{}' has no ability score like (30/10/10)".format(description)
        return tuple(int(s) for s in match.group().split("/"))

    @staticmethod
    def __match_ability_score(description: str) -> re.Match:
        return re.search(r'[-+]?[\d]+/[-+]?[\d]+/[-+]?[\d]+', description)

    @staticmethod
    def valid(line: str) -> bool:
        if Racer.__match_ability_score(line):
            return True
        return False


class RollResult:
    def __init__(self, line: str):
        assert RollResult.valid(line)

        # FIXME: Now we just grab the digit from the back.
        match = re.search(r'\d+$', line.strip())
        assert match, "Could not find dice result from line '{}'".format(line)

        self.number = int(match.group())

    @staticmethod
    def valid(line: str) -> bool:
        line = line.rstrip()
        if len(line) == 0:
            return False
        return line.startswith("ROLL : ") and line[-1].isdigit()


def __sort_racer(iterable: List[Tuple[Racer, RollResult]]) -> List[Tuple[Racer, RollResult]]:
    return sorted(iterable, key=lambda pair: pair[1].number, reverse=True)

def __stringfy_speed(iterable: List[Tuple[Racer, RollResult]], original: List[Tuple[Racer, RollResult]], is_item_area: bool) -> str:
    ans = []
    original_racer_order = [racer for racer, _ in original]
    for i, (racer, roll) in enumerate(iterable):
        description = racer.description.strip()
        if is_item_area and i > len(iterable) // 2 - 1:
            if roll.number % 10 in [7, 8]:
                description = "[加速道具]" + description
            if roll.number % 10 == 9:
                description = "[攻击道具]" + description
        if i > original_racer_order.index(racer):
            description = description + "--"
        if i < original_racer_order.index(racer):
            description = description + "++"
        ans.append(description)

    return "\n".join(ans)

def __assert_valid_order(order: List[Tuple[Racer, RollResult]]):
    for racer, roll in order:
        assert isinstance(racer, Racer) and isinstance(roll, RollResult)


def __object_from_line(line: str):
    line = line.strip("\n")
    for obj_type in [RollResult, Racer]:
        if obj_type.valid(line):
            return obj_type(line)
    return None


def __parse_item_from_raw_string(raw: str) -> List:
    objects = []
    for line in raw.split("\n"):
        matched = __object_from_line(line)
        if matched:
            objects.append(matched)
    return objects


def __create_order_from_string(item_string: str):
    objects = __parse_item_from_raw_string(item_string)
    order = list(zip(objects[::2], objects[1::2]))
    __assert_valid_order(order)
    return order


def parse_speed(item_string: str, is_item_area: bool) -> str:
    original_order = __create_order_from_string(item_string)
    new_order = __sort_racer(original_order)
    return __stringfy_speed(new_order, original_order, is_item_area)


def __stringfy_duel(racers):
    ans = []
    ans.append("[collapse=决斗骰点]")
    for i, racer in enumerate(racers[:-1]):
        next_racer = racers[i+1]
        ans.append(racer.description)
        ans.append("守：[dice]d{}+{}[/dice]".format(100 - racer.defence(), racer.defence()))
        ans.append("攻：[dice]d{}+{}[/dice]".format(100 - next_racer.attack(), next_racer.attack()))
    ans.append(racers[-1].description)
    ans.append("[/collapse]")
    return "\n\n".join(ans)


def gen_duel(duel_string: str) -> str:
    objects = __parse_item_from_raw_string(duel_string)
    for obj in objects:
        assert isinstance(obj, Racer)
    if len(objects) == 1:
        return objects[0].description
    return __stringfy_duel(objects)

def __stringfy_race(racers) -> str:
    ans = []
    ans.append("[collapse=竞速骰点]")
    racer_count = len(racers)
    for i, racer in enumerate(racers):
        ans.append(racer.description)
        ans.append("[dice]d{}+{}+{}[/dice]".format(100 - racer.speed(), racer.speed(), 15*(racer_count-i-1)))
    ans.append("[/collapse]")
    return "\n\n".join(ans)
        
def gen_speed(race_string: str) -> str:
    objects = __parse_item_from_raw_string(race_string)
    for obj in objects:
        assert isinstance(obj, Racer)
    return __stringfy_race(objects)

def __stringfy_parse_duel(objects) -> str:
    ans = []
    defence = None
    attack = None
    ans.append(objects[0].description)
    for i, obj in enumerate(objects[1:]):
        if i % 3 == 0:
            defence = obj.number
        if i % 3 == 1:
            attack = obj.number
        if i % 3 == 2:
            desc = obj.description
            if attack > defence:
                desc = "+" + desc
            else:
                desc = "\n" + desc
            ans.append(desc)
    return "\n".join(ans)
    


def parse_duel(duel_string: str) -> str:
    objects = __parse_item_from_raw_string(duel_string)
    for i, obj in enumerate(objects):
        if i % 3 == 0:
            assert isinstance(obj, Racer)
        else:
            assert isinstance(obj, RollResult)
    return __stringfy_parse_duel(objects)

def __stringfy_duel_detail(racers) -> str:
    ans = []
    dogfight = len(racers) > 2
    ans.append("[collapse=决斗细节]")
    if dogfight:
        ans.append("多人混战（攻击+防御）：")
    else:
        ans.append("决斗（攻击 vs 防御）：")
    defender = True
    for r in racers:
        ans.append(r.description)
        if dogfight:
            base = r.attack() + r.defence()
        else:
            if defender:
                base = r.defence()
                defender = False
            else:
                base = r.attack()
        ans.append("[dice]d{}+{}[/dice]".format(100 - base, base))
    ans.append("[/collapse]")
    return "\n\n".join(ans)

def gen_duel_detail(string: str) -> str:
    objects = __parse_item_from_raw_string(string)
    for obj in objects:
        assert isinstance(obj, Racer)
    return __stringfy_duel_detail(objects)



def read_stdin_as_string() -> str:
    return "\n".join(sys.stdin)

def main(args):
    if args.test:
        test()
        return

    stdin = read_stdin_as_string()
    if args.parse_speed:
        print(parse_speed(stdin, is_item_area=False))
    elif args.parse_speed_with_item:
        print(parse_speed(stdin, is_item_area=True))
    elif args.parse_duel:
        print(parse_duel(stdin))
    elif args.gen_duel:
        print(gen_duel(stdin))
    elif args.gen_speed:
        print(gen_speed(stdin))
    elif args.gen_duel_detail:
        print(gen_duel_detail(stdin))


def test_racer_object():
    LINE_GIVEN = "[加速道具]豪华摩托，雅木茶 & 饺子，(20/10/0)--"
    DESCRIPTION_EXPECTED = "豪华摩托，雅木茶 & 饺子，(20/10/0)"
    ABILITY_SCORE_EXPECTED = (20, 10, 0)

    assert Racer.valid(LINE_GIVEN) == True

    r = Racer(LINE_GIVEN)
    assert r.description == DESCRIPTION_EXPECTED
    assert r.ability_score == ABILITY_SCORE_EXPECTED

    GARBAGE_LINE = "Line without ability score."
    try:
        Racer(GARBAGE_LINE)
    except AssertionError:
        pass

    assert Racer.valid(GARBAGE_LINE) == False

def test_roll_result_object():
    LINE_GIVEN = "ROLL : d100+100=d100(81)+100=181"

    assert RollResult(LINE_GIVEN).number == 181
    assert RollResult.valid(LINE_GIVEN) == True

    for INVALID_LINE in [
        "Invalid line.",
        "ROLL : ",
    ]:
        try:
            RollResult(INVALID_LINE)
        except AssertionError:
            pass
        assert RollResult.valid(INVALID_LINE) == False

PARSE_SPEED_GIVEN = """
豪华摩托，雅木茶 & 饺子，(20/10/0)

ROLL : d80+20+140=d80(57)+20+140=217


战车加西亚号，肯 & 蕾娜，(30/0/20)

ROLL : d70+30+120=d70(69)+30+120=219

Z 滑翔翼，娜乌西卡 & 卡缪，(20/0/20)

ROLL : d80+20+80=d80(70)+20+80=169

废土战车，喽啰们，(0/20/10)

ROLL : d100+100=d100(81)+100=178


https://nga.178.com/read.php?&tid=33412021&pid=645545471&to=1

https://nga.178.com/read.php?&tid=33412021&pid=645545471&to=1

https://nga.178.com/read.php?&tid=33412021&pid=645545471&to=1
"""

PARSE_SPEED_EXPECTED = """战车加西亚号，肯 & 蕾娜，(30/0/20)++
豪华摩托，雅木茶 & 饺子，(20/10/0)--
废土战车，喽啰们，(0/20/10)++
Z 滑翔翼，娜乌西卡 & 卡缪，(20/0/20)--"""


PARSE_SPEED_ITEM_AREA_EXPECTED = """战车加西亚号，肯 & 蕾娜，(30/0/20)++
豪华摩托，雅木茶 & 饺子，(20/10/0)--
[加速道具]废土战车，喽啰们，(0/20/10)++
[攻击道具]Z 滑翔翼，娜乌西卡 & 卡缪，(20/0/20)--"""


GEN_DUEL_GIVEN = PARSE_SPEED_EXPECTED + """
https://nga.178.com/read.php?&tid=33412021&pid=645545471&to=1

https://nga.178.com/read.php?&tid=33412021&pid=645545471&to=1

https://nga.178.com/read.php?&tid=33412021&pid=645545471&to=1
"""


GEN_DUEL_EXPECTED = """[collapse=决斗骰点]

战车加西亚号，肯 & 蕾娜，(30/0/20)

守：[dice]d80+20[/dice]

攻：[dice]d90+10[/dice]

豪华摩托，雅木茶 & 饺子，(20/10/0)

守：[dice]d100+0[/dice]

攻：[dice]d80+20[/dice]

废土战车，喽啰们，(0/20/10)

守：[dice]d90+10[/dice]

攻：[dice]d100+0[/dice]

Z 滑翔翼，娜乌西卡 & 卡缪，(20/0/20)

[/collapse]"""

GEN_SPEED_GIVEN = GEN_DUEL_GIVEN

GEN_SPEED_EXPECTED = """[collapse=竞速骰点]

战车加西亚号，肯 & 蕾娜，(30/0/20)

[dice]d70+30+60[/dice]

豪华摩托，雅木茶 & 饺子，(20/10/0)

[dice]d80+20+40[/dice]

废土战车，喽啰们，(0/20/10)

[dice]d100+0+20[/dice]

Z 滑翔翼，娜乌西卡 & 卡缪，(20/0/20)

[dice]d80+20+0[/dice]

[/collapse]"""

PARSE_DUEL_GIVEN = """
豪华摩托，雅木茶 & 饺子，(20/10/0)

守：
ROLL : d100+0=d100(25)+0=25


攻：
ROLL : d100+0=d100(77)+0=77


战车加西亚号，肯 & 蕾娜，(30/0/20)

守：
ROLL : d80+20=d80(24)+20=44


攻：
ROLL : d100+0=d100(56)+0=56


可变机车新希望号，艾文·艾里安 & 黛安娜，(30/0/10)

守：
ROLL : d90+10=d90(21)+10=31


攻：
ROLL : d100+0=d100(51)+0=51


Z 滑翔翼，娜乌西卡 & 卡缪，(20/0/20)

https://nga.178.com/read.php?&tid=33412021&pid=646199752&to=1

https://nga.178.com/read.php?&tid=33412021&pid=646199752&to=1

https://nga.178.com/read.php?&tid=33412021&pid=646199752&to=1
"""

PARSE_DUEL_EXPECTED = """豪华摩托，雅木茶 & 饺子，(20/10/0)
+战车加西亚号，肯 & 蕾娜，(30/0/20)
+可变机车新希望号，艾文·艾里安 & 黛安娜，(30/0/10)
+Z 滑翔翼，娜乌西卡 & 卡缪，(20/0/20)"""


def test_parse_speed():
    assert parse_speed(PARSE_SPEED_GIVEN, is_item_area=True) == PARSE_SPEED_ITEM_AREA_EXPECTED
    assert parse_speed(PARSE_SPEED_GIVEN, is_item_area=False) == PARSE_SPEED_EXPECTED

def test_gen_duel():
    assert gen_duel(GEN_DUEL_GIVEN) == GEN_DUEL_EXPECTED

def test_gen_speed():
    assert gen_speed(GEN_SPEED_GIVEN) == GEN_SPEED_EXPECTED

def test_parse_duel():
    assert parse_duel(PARSE_DUEL_GIVEN) == PARSE_DUEL_EXPECTED

def test():
    test_racer_object()
    test_roll_result_object()
    test_parse_speed()
    test_parse_duel()
    test_gen_duel()
    test_gen_speed()

if __name__ == "__main__":
    p = ArgumentParser("ofey404's TRPG car race script.")
    p.add_argument("--test", action="store_true", help="Test the script.")
    p.add_argument("--parse_speed_with_item", action="store_true", help="Calculate item area.")
    p.add_argument("--parse_speed", action="store_true", help="Calculate race area.")
    p.add_argument("--parse_duel", action="store_true", help="Calculate race area.")
    p.add_argument("--gen_duel", action="store_true", help="Calculate duel area.")
    p.add_argument("--gen_duel_detail", action="store_true", help="Calculate duel area.")
    p.add_argument("--gen_speed", action="store_true", help="Calculate race area.")
    main(p.parse_args())
