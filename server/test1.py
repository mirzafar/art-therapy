from pymystem3 import Mystem

from utils.lists import ListUtils

a = ' гнев, вина, одиноко, страдаю, боюсь, ненавижу, бесполезео, страх, печаль, безнадежность, нет смысла, нет цели, мучаюсь, недостоин, виноват, тяжело, невыносимо'
v = a.split(',')

m = Mystem()
e = []
for i in v:
    q = ListUtils.to_list_of_strs(m.lemmatize(i))
    e.append(q)

print(e)
