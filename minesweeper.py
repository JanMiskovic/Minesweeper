import random
from os import system
from msvcrt import getch

from termcolor import colored
from tail_recursive import tail_recursive


# --------- Utilities -----------------------------------------------------------------------------


def vycisti_terminal():
    system("cls||clear")


def skry_kurzor():
    print('\033[?25l', end='')


def zobraz_kurzor():
    print('\033[?25h', end='')


# Presunie kurzor na vrch terminálu
# (vhodné na opakované vykreslovanie bez blikania).
def vrch_terminalu():
    print('\x1b[F' * 50)


# Vytlačí ľubovoľné množstvo stringov s odsadením na ľavej strane.
def padded_print(*strings, sep="\n    ", end='\n'):
    print("    ", end='')
    print(*strings, sep=sep, end=end)


# Zistí, či sú dané indexy v rámci zadaného dvojrozmerného poľa.
def v_ramci_pola(i, j, pole):
    return (0 <= i < len(pole)) and (0 <= j < len(pole[0]))


# Vráti nové dvojrozmerné pole s požadovanou veľkosťou a prvkami.
# prvok je funkcia, ktorá na základe riadku a stĺpca vracia určitú hodnotu.
def nova_matica(riadky, stlpce, prvok):
    return tuple(tuple(prvok(i, j) for j in range(stlpce)) for i in range(riadky))


# Vráti nové dvojrozmerné pole s nahradeným prvkom.
def nahrad_prvok(riadok, stlpec, novy_prvok, pole):
    def prvok(i, j, r=riadok, s=stlpec, np=novy_prvok):
        return np if (i, j) == (r, s) else pole[i][j]
    
    return nova_matica(len(pole),len(pole[0]), prvok)


# Vráti susedné prvky, alebo súradnice, ktoré sú v medziach poľa.
# Parametre: riadok a stĺpec, okolo ktorého hľadáme,
# pole, v ktorom hľadáme, suradnice = chceme súradnice namiesto prvkov.
def ziskaj_susedov(riadok, stlpec, pole, suradnice=False):
    return tuple((i, j) if suradnice else pole[i][j]
                 for i in range(riadok - 1, riadok + 2)
                 for j in range(stlpec - 1, stlpec + 2)
                 if (i, j) != (riadok, stlpec) and v_ramci_pola(i, j, pole))


# --------- Logika hry ----------------------------------------------------------------------------


# Vráti náhodne vygenerované 2-rozmerné pole s pozíciami mín
# a očíslovanýmí bunkami podľa susedných mín.
# Parametre: požadovaný počet riadkov, stĺpcov, mín, seed náhodných čísiel.

def nove_minove_pole(riadky, stlpce, pocet_min, seed=None):
    # Funkcie pracujúce s náhodnými hodnotami nemôžeme považovať za úplne 'čisté',
    # pridanie parametru seed, ktorý ovplyvní náhodné hodnoty, aby boli podľa potreby vždy rovnaké,
    # je dobrou strednou cestou medzi zachovaním pointy hry, a držaním sa funkcionálnej paradigmy.

    random.seed(seed)

    vsetky_pozicie = tuple((i, j) for i in range(riadky) for j in range(stlpce))
    pozicie_min = nahodne_pozicie_min(tuple(), vsetky_pozicie, pocet_min)
    
    # Vytvoríme 2-rozmerné pole s hviezdičkami pre míny.
    minove_pole = nova_matica(riadky, stlpce, lambda i, j, p=pozicie_min: '*' if (i, j) in p else ' ')

    # Vrátime finálne 2-rozmerné pole, s hviezdičkami na pozíciach mín,
    # ' ' na pozíciach bez susedných mín, a číslom vyjadrujúcim počet susedných mín na zvyšných pozíciach.
    return nova_matica(riadky, stlpce, lambda i, j, m=minove_pole: pocet_susednych_min(i, j, m))


# Z dvojprvkových tuples reprezentujúcich pozície v 2D poli
# náhodne vyberie požadovaný počet pozícii pre míny a vráti ich.

@tail_recursive
def nahodne_pozicie_min(vybrane_pozicie, volne_pozicie, zvysne_miny):
    if zvysne_miny == 0:
        return vybrane_pozicie
    else:
        nova_nahodna_pozicia = random.choice(volne_pozicie)
        nove_vybrane_pozicie = (*vybrane_pozicie, nova_nahodna_pozicia)
        zostavajuce_pozicie = tuple(i for i in volne_pozicie if i != nova_nahodna_pozicia)
        # Ekvivalent tuple(filter(lambda x, n=nova_nahodna_pozicia: x != n, volne_pozicie)).
        
        return nahodne_pozicie_min.tail_call(nove_vybrane_pozicie, zostavajuce_pozicie, zvysne_miny - 1)


# Zistí počet mín okolo bunky.
# Parametre: riadok a stĺpec, na ktorom sa bunka nachádza,
# mínové pole, v ktorom chceme susedné míny hladať.

def pocet_susednych_min(riadok, stlpec, minove_pole):
    # Ak je bunka mína, susedné míny nemusíme hladať.
    if minove_pole[riadok][stlpec] == '*':
        return '*'
    else:
        susedia = ziskaj_susedov(riadok, stlpec, minove_pole)
        pocet_min = susedia.count('*')
        # Ak je počet susedných mín 0, vrátime ' '.
        return pocet_min or ' '


# Vráti nové viditeľné pole s požadovanou odokrytou / vlajkou označenou bunkou.
# Parametre: riadok a stĺpec, ktorý chceme odokryť / označiť, vlajka (True / False),
# mínové pole a viditeľné pole, ktorých sa zmena týka.

def nove_viditelne_pole(riadok, stlpec, vlajka, minove_pole, viditelne_pole):
    realny_prvok = minove_pole[riadok][stlpec]
    viditelny_prvok = viditelne_pole[riadok][stlpec]

    if vlajka:
        if viditelny_prvok in ('#', 'F'):
            # Ak na vybranej pozícii už je vlajka, dáme ju preč.
            novy_prvok = '#' if viditelny_prvok == 'F' else 'F'
            # Vrátime nové 2-rozmerné pole s vlajkou / odstránenou vlajkou na vybranej pozícii.
            return nahrad_prvok(riadok, stlpec, novy_prvok, viditelne_pole)
        # Ak sa pokúsime dať vlajku na už odokrytú pozíciu, nič sa nezmení (vráti sa originálne vid. pole).
        else: return viditelne_pole

    # Ak je pozícia už odokrytá, a vyberieme číslo, ktoré sa rovná počtu vlajok na
    # susedných pozíciach čísla, odokryjeme všetky skryté susedné prvky (akord), inak sa nič nezmení.

    elif realny_prvok == viditelny_prvok:
        pocet_sus_vlajok = ziskaj_susedov(riadok, stlpec, viditelne_pole).count('F')
        if isinstance(realny_prvok, int) and realny_prvok == pocet_sus_vlajok:
            suradnice_susedov = ziskaj_susedov(riadok, stlpec, viditelne_pole, suradnice=True)
            skryti_susedia = tuple((i, j) for i, j in suradnice_susedov if viditelne_pole[i][j] == '#')
            return odokry_pozicie(skryti_susedia, minove_pole, viditelne_pole)
        else: return viditelne_pole

    # Ak je odokrytá bunka prázdna, zavoláme rekurzívnu funkciu,
    # ktorá odokryje všetky susedné bunky.

    elif realny_prvok == ' ':
        nove_viditelne = nahrad_prvok(riadok, stlpec, realny_prvok, viditelne_pole)
        suradnice_susedov = ziskaj_susedov(riadok, stlpec, viditelne_pole, suradnice=True)
        skryti_susedia = tuple((i, j) for i, j in suradnice_susedov if viditelne_pole[i][j] == '#')
        return odokry_pozicie(skryti_susedia, minove_pole, nove_viditelne)

    else:
        # Vrátime nové viditeľne pole s odokrytou bunkou.
        return nahrad_prvok(riadok, stlpec, realny_prvok, viditelne_pole)


# Vráti nové viditelné pole, kde sú rekurzívne odokryté všetky požadované pozície.
@tail_recursive
def odokry_pozicie(pozicie, minove_pole, viditelne_pole):
    if not pozicie:
        return viditelne_pole
    else:
        # Odokryjeme jednu pozíciu zo zoznamu pozícii na odokrytie.
        nove_viditelne = nove_viditelne_pole(*pozicie[0], False, minove_pole, viditelne_pole)
        return odokry_pozicie.tail_call(pozicie[1:], minove_pole, nove_viditelne)


# Skontroluje, či nebola odokrytá mína (prehra).
def skontroluj_prehru(viditelne_pole):
    return any('*' in riadok for riadok in viditelne_pole)


# Skontroluje, či sú odokryté všetky bunky okrem mín (výhra).
def skontroluj_vyhru(viditelne_pole, pocet_min):
    pocet_skrytych = sum(prvok in ('#', 'F') for riadok in viditelne_pole for prvok in riadok)
    return pocet_skrytych == pocet_min


# --------- Vstup a výstup ------------------------------------------------------------------------


# Zafarbí, naformátuje a vytlačí 2-rozmerné mínové pole do terminálu.
def vytlac_pole(pole, aktualna_pozicia=None):
    vrch_terminalu()

    riadky = len(pole)
    stlpce = len(pole[0])

    nadpis = f"    {colored('MINESWEEPER', 'cyan')}\n"
    nazvy_stlpcov = f"      {''.join(f'{i + 1: <4}' for i in range(stlpce))}"
    horna_hrana = f"    ╔{'═══╦' * (stlpce - 1)}═══╗"
    dolna_hrana = f"    ╚{'═══╩' * (stlpce - 1)}═══╝"
    medzi_riadky = f"\n    ╠{'═══╬' * (stlpce - 1)}═══╣\n"

    farby = {1: "cyan", 2: "green", 3: "red", 4: "yellow",
             5: "blue", 6: "magenta", 7: "blue", 8: "magenta",
             '#': None, ' ': None, '*': "white", 'F': "white"}

    pozadia = {'*': "on_red", 'F': "on_red"}

    # Prvok si pomocou knižnice termcolor zmeníme na špeciálny string,
    # ktorý bude po vytlačení do terminálu zafarbený.

    def zafarbi_prvok(i, j, ap=aktualna_pozicia, p=pole, f=farby, pz=pozadia):
        prvok = p[i][j]
        # Kurzor.
        if ap is not None and (i, j) == ap:
            return colored(prvok, "white", "on_cyan")
        else:
            return colored(prvok, f.get(prvok), pz.get(prvok))

    # Riadky spojíme do stringu. # Zarovnané číslo riadku. # Všetky prvky spojíme ' ║ ' a riadok ohraničíme '║' z oboch strán
    stred = medzi_riadky.join(f'{i + 1: >3} ║ ' + ' ║ '.join(zafarbi_prvok(i, j) for j in range(stlpce)) + ' ║'
                              for i in range(riadky))

    # Vytlačíme finálne naformátované stringy.
    print(nadpis, nazvy_stlpcov, horna_hrana, stred, dolna_hrana, sep='\n')
    return None


# Získa, ošetrí a vráti novú aktuálnu pozíciu.
# Parametre: aktuálna pozícia v poli, pole, v ktorom sa chceme pohnúť.

@tail_recursive
def ziskaj_pohyb(aktualna_pozicia, pole):
    riadok, stlpec = aktualna_pozicia
    smery = {'w': (riadok - 1, stlpec),
             's': (riadok + 1, stlpec),
             'a': (riadok, stlpec - 1),
             'd': (riadok, stlpec + 1)} 

    prvy_vstup = str(getch()).strip('b\'')

    # Šípky sú kombináciou špeciálneho symbolu \xe0 a písmen H, P, K, M.
    # Ak je na vstupe tento špeciálny symbol, načítame si aj ďalší charakter,
    # a premeníme písmena HPKM na wsad.

    vstup = prvy_vstup \
            if prvy_vstup != '\\xe0' \
            else str(getch()).strip('b\'').translate(str.maketrans("HPKM", "wsad")).lower()

    if vstup == '\\x03':  # Ctrl + C
        raise KeyboardInterrupt

    # F a V označí / odznačí aktuálnu pozíciu vlajkou.
    elif vstup in "fv":
        return aktualna_pozicia, "vlajka"

    # Medzera a Enter odokryje aktuálnu pozíciu.
    elif vstup in (' ', '\\r'):
        return aktualna_pozicia, "odokry"

    elif vstup in "wsad" and v_ramci_pola(*smery[vstup], pole):
        return smery[vstup], "pohyb"

    else:
        # Ak stlačená klávesa nezodpovedá žiadnej akcii, čakáme na vstup znovu.
        return ziskaj_pohyb.tail_call(aktualna_pozicia, pole)


# Získa a ošetrí používateľom zadanú obťažnosť.
# Vráti počet riadkov, stĺpcov a mín podľa vybratej obťažnosti.

@tail_recursive
def ziskaj_obtaznost():
    zobraz_kurzor()
    vstup = input("\n    Vyberte si obťažnosť: ").strip()
    skry_kurzor()

    if len(vstup) != 1 or not vstup.isnumeric() or not int(vstup) in (1, 2, 3):
        padded_print(colored("Obťažnosť musí byť číslo 1, 2, alebo 3.",
                             "white", "on_red"))
        return ziskaj_obtaznost.tail_call()
    else:
        obtaznost = int(vstup) - 1
        riadky = (9, 16, 16)
        stlpce = (9, 16, 30)
        miny = (10, 40, 100)
        return riadky[obtaznost], stlpce[obtaznost], miny[obtaznost]


# Vypíše výsledok hry, a zistí či chce používateľ hrať znovu.

def hrat_znovu(vyhral, minove_pole):
    vytlac_pole(minove_pole)
    padded_print('', (colored("Gratulujeme! Úspešne ste odokryli všetky polia.", "white", "on_green"))
                 if vyhral else (colored("Ow :( Narazili ste na mínu.", "white", "on_red")))

    zobraz_kurzor()
    vstup = input("    Prajete si hrať znovu? "
               + f"({colored('áno', 'white', 'on_green')} / "
               + f"{colored('nie', 'white', 'on_red')}): ")
    skry_kurzor()
    return vstup.strip().lower() in ("áno", "ano", "a")


# --------- Inicializácia a herná slučka ----------------------------------------------------------


# Začiatok programu. Incializuje hru a spustí hernú slučku.
@tail_recursive
def zacni_hru():
    vycisti_terminal()
    padded_print('', colored("MINESWEEPER\n", "cyan"),
                 "Cieľ hry:      Odokryť všetky bunky, okrem tých, ktoré skrývajú míny.\n",
                 "Pravidlá:      Číslo zobrazené v odokrytej bunke reprezentuje počet mín v ôsmich susedných bunkách.",
                 "               Bunka, ktorá nemá susedné míny je prázdna a po jej odokrytí sa odokryjú aj všetky susedné bunky.",
                 "               Ak si myslíme, že bunka skrýva mínu, môžeme ju označiť vlajkou.",
                 "               Ak znovu odokryjeme už odokrytú bunku, ktorej číslo sa rovná počtu vlajok na susedných bunkách,",
                 "               odokryjú sa všetky susedné bunky bez vlajok (tzv. 'akord', môžeme odokryť viac buniek naraz).\n",
                 "Ovládanie:     WASD a šípky - pohyb v bludisku.",
                 "               F a V - položenie / odstránenie vlajky.",
                 "               Medzerník a Enter - odokrytie bunky.\n",
                 "Obťažnosťi:    (1) 9x9 pole,   10 mín.",
                 "               (2) 16x16 pole, 40 mín.",
                 "               (3) 30x16 pole, 99 mín.")

    riadky, stlpce, pocet_min = ziskaj_obtaznost()
    vycisti_terminal()

    minove_pole = nove_minove_pole(riadky, stlpce, pocet_min)
    # V prvom viditeľnom poli bude všetko skryté.
    viditelne_pole = nova_matica(riadky, stlpce, lambda i, j: '#')
    pociatocna_pozicia = (riadky // 2, stlpce // 2)

    # Spusti hernú slučku.
    # Ak vráti True, začni ďalšiu hru, inak ukonči program.
    if herna_slucka(pociatocna_pozicia, minove_pole, viditelne_pole, pocet_min):
        return zacni_hru.tail_call()
    else:
        return None


# Herná slučka, opakuje sa kým hráč neprehrá / nevyhrá.
# Parametre: aktuálna pozícia v poli, mínové pole, aktuálne viditeľné pole, počet mín.

@tail_recursive
def herna_slucka(aktualna_pozicia, minove_pole, viditelne_pole, pocet_min):
    vytlac_pole(viditelne_pole, aktualna_pozicia)
    nova_pozicia, akcia = ziskaj_pohyb(aktualna_pozicia, viditelne_pole)

    if akcia == "pohyb":
        return herna_slucka.tail_call(nova_pozicia, minove_pole, viditelne_pole, pocet_min)

    elif akcia == "vlajka":
        nove_viditelne = nove_viditelne_pole(*nova_pozicia, True, minove_pole, viditelne_pole)
        return herna_slucka.tail_call(aktualna_pozicia, minove_pole, nove_viditelne, pocet_min)

    else: # Akcia == odokry
        nove_viditelne = nove_viditelne_pole(*nova_pozicia, False, minove_pole, viditelne_pole)

        if skontroluj_prehru(nove_viditelne):
            return hrat_znovu(False, minove_pole)

        elif skontroluj_vyhru(nove_viditelne, pocet_min):
            return hrat_znovu(True, minove_pole)

        else:
            return herna_slucka.tail_call(aktualna_pozicia, minove_pole, nove_viditelne, pocet_min)


# Ak modul priamo spúštame (neimportujeme), spustíme hru.
if __name__ == "__main__":
    zacni_hru()
