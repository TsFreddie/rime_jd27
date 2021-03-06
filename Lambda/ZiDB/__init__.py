import os
import re
from PinyinConsts import VALID_PY

UNDEFINED = 0       # 未定义
GENERAL = 1         # 通常
SUPER = 2           # 超级
HIDDEN = 3          # 无理

class Zi:
    def __init__(self, line, which=HIDDEN):
        data = line.split('\t')
        self._char = data[0]
        self._rank = int(data[1])
        self._shape = data[2]
        self._pinyins = []
        self._type = which
        self._comment = None
        for i in range(3, len(data) - 1, 2):
            self._pinyins.append((data[i], int(data[i+1])))
        
        if (len(data) % 2 == 0):
            self._comment = data[-1]

    def __hash__(self):
        return hash(self._char)

    def pinyins(self):
        result = set()
        for entry in self._pinyins:
            result.add(entry[0])
        return result

    def char(self):
        return self._char

    def weights(self):
        return self._pinyins
    
    def shape(self):
        return self._shape

    def rank(self):
        return self._rank

    def which(self):
        return self._type

    def comment(self):
        if self._comment is None:
            return ''
        return self._comment
    
    def line(self):
        line = '%s\t%d\t%s' % (self._char, self._rank, self._shape)
        for pinyin in self._pinyins:
            line += '\t%s\t%d' % pinyin
        if self._comment is not None:
            line += '\t%s' % self._comment
        return line

    def add_pinyins(self, pinyins):
        """
        为单字添加拼音
        ----------
        pinyins: list[tuple(py: str, len: int)]
            需要添加的拼音
        """
        existing = self.pinyins()
        for pinyin in pinyins:
            py = pinyin[0]
            assert py in VALID_PY, '`%s`字拼音`%s`不合法' % (self._char, py)
            if py not in existing:
                self._pinyins.append(pinyin)
    
    def change_shape(self, shape):
        """
        更换单字形码
        ----------
        shape: str
            形码
        """
        assert re.search("^[aiouv]{3,4}$", shape), '`%s`字形码不合法`(%s)`' % (self._char, shape)
        self._shape = shape

    def change_rank(self, rank):
        """
        更换单字全码排序
        ----------
        rank: int
            全码权值
        """
        self._rank = rank

    def change_which(self, which):
        """
        更换单字隶属码表
        ----------
        which: ZiDB.GENERAL | ZiDB.SUPER
            通常表 | 超级表
        """
        self._which = which

    def change_code_length(self, pinyins, length):
        """
        更换单字简码长度
        ----------
        pinyins: set(str)
            需要修改的拼音
        length: int
            码长
        """
        
        for i in range(len(self._pinyins)):
            weight = self._pinyins[i]
            if weight[0] in pinyins:
                self._pinyins[i] = (weight[0], length)

    def remove_pinyins(self, pinyins):
        og_pinyins = self._pinyins
        self._pinyins = []

        for pinyin in og_pinyins:
            if pinyin[0] not in pinyins:
                self._pinyins.append(pinyin)

_db = {}
_fixed = []

_path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_path, '通常.txt'), mode='r', encoding='utf-8') as f:
    for line in f:
        char = Zi(line.strip(), GENERAL)
        _db[char._char] = char

with open(os.path.join(_path, '超级.txt'), mode='r', encoding='utf-8') as f:
    for line in f:
        char = Zi(line.strip(), SUPER)
        if (char._char in _db):
            print('警告，通常字和超级字重复：', char.char())
        else:
            _db[char._char] = char

with open(os.path.join(_path, '无理.txt'), mode='r', encoding='utf-8') as f:
    for line in f:
        char = Zi(line.strip(), HIDDEN)
        if (char._char in _db):
            print('警告，通常字和无理字重复：', char.char())
        else:
            _db[char._char] = char

with open(os.path.join(_path, '通常特定.txt'), mode='r', encoding='utf-8') as f:
    for entry in f:
        line = entry.strip()
        if (len(line) <= 0 or line.startswith('#')):
            continue

        data = line.split('\t')
        _fixed.append((data[0], data[1], GENERAL))

with open(os.path.join(_path, '超级特定.txt'), mode='r', encoding='utf-8') as f:
    for entry in f:
        line = entry.strip()
        if (len(line) <= 0 or line.startswith('#')):
            continue

        data = line.split('\t')
        _fixed.append((data[0], data[1], SUPER))

def get(char):
    if char not in _db:
        return None
    return _db[char]

def all():
    return _db.values()

def fixed():
    return _fixed

def add(char, shape, pinyins, rank, which = HIDDEN, comment = None):
    """
    添加单字到字库
    ----------
    char : str
        需要添加的单字
    shape: str
        形码
    pinyins: list[tuple(py: str, len: int)]
        拼音
    rank: int
        全码权值
    which: ZiDB.GENERAL | ZiDB.SUPER
        通常表 | 超级表
    comment: str
        注释
    """

    assert len(char) == 1, '`%s`不是单字' % char
    assert re.search("^[aiouv]{3,4}$", shape), '`%s`字形码不合法`(%s)`' % (char, shape)
    assert char not in _db, '`%s`字已存在' % char
    assert len(pinyins) != 0, '`%s`字没有提供拼音' % char

    for pinyin in pinyins:
        assert pinyin[0] in VALID_PY, '`%s`字拼音`%s`不合法' % (char, pinyin[0])

    line = '%s\t%d\t%s' % (char, rank, shape)
    for pinyin in pinyins:
        line += '\t%s\t%d' % pinyin
    if comment is not None:
        line += '\t%s' % comment
    _db[char] = Zi(line, which)
    return _db[char]


def remove(char, pinyins):
    """
    删除单字拼音，如果空音则彻底删除
    ----------
    char : str
        目标单字
    pinyins: set(str)
        需要删除的拼音
    """

    assert char in _db, '`%s`字不存在' % char
    _db[char].remove_pinyins(pinyins)

    if len(_db[char].pinyins()) <= 0:
        del _db[char]

def commit():
    all_char = sorted(all(), key=lambda x: x._char)
    danzi = open(os.path.join(_path, '通常.txt'), mode='w', encoding='utf-8', newline='\n')
    chaoji = open(os.path.join(_path, '超级.txt'), mode='w', encoding='utf-8', newline='\n')
    hidden = open(os.path.join(_path, '无理.txt'), mode='w', encoding='utf-8', newline='\n')

    for zi in all_char:
        if zi.which() == GENERAL:
            danzi.write(zi.line()+'\n')
        elif zi.which() == SUPER:
            chaoji.write(zi.line()+'\n')
        else:
            hidden.write(zi.line()+'\n')
    
    danzi.close()
    chaoji.close()
    hidden.close()
