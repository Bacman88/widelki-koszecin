import json
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table,TableStyle,Paragraph,Frame,Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
F='fonts/'
pdfmetrics.registerFont(TTFont('I',F+'Inter-Regular.ttf'));pdfmetrics.registerFont(TTFont('IS',F+'Inter-SemiBold.ttf'));pdfmetrics.registerFont(TTFont('IB',F+'Inter-Bold.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('I',normal='I',bold='IB',italic='I',boldItalic='IB')
W,H=landscape(A3);M=40
G=colors.HexColor('#00463c');LIME=colors.HexColor('#e6f5c8');INK=colors.HexColor('#10201c');MUT=colors.HexColor('#5b6b66');RULE=colors.HexColor('#dfe7e3')
LC={'1':'#00704f','2':'#1f6fd1','3':'#c98a00','4':'#d4473a'}
LN={'1':'Piasek – Płaszczymąka – Bukowiec – Strzebiń Lubliniecka – Koszęcin Rynek – Irki – Wierzbie – Sadów – Lubliniec PKP','2':'Boronów – Boronów PKP – Koszęcin Rynek – Koszęcin PKP – Brusiek – Kalety PKP','3':'Lisów PKP – Chwostek – Doły – Cieszowa – Koszęcin Rynek – Koszęcin PKP','4':'Łazy – Strzebiń Szkoła – Strzebiń Lubliniecka – Koszęcin Rynek – Irki – Wierzbie – Rusinowice PKP – Piłka'}
P=ParagraphStyle('p',fontName='I',fontSize=12.5,leading=18,textColor=INK,spaceAfter=7)
PS=ParagraphStyle('ps',parent=P,fontSize=10.5,leading=14.5,textColor=MUT)
H2=ParagraphStyle('h2',fontName='IB',fontSize=20,leading=24,textColor=INK,spaceAfter=10,spaceBefore=4)
H3=ParagraphStyle('h3',fontName='IB',fontSize=14.5,leading=19,textColor=INK,spaceAfter=6,spaceBefore=8)
BL=ParagraphStyle('bl',parent=P,leftIndent=14,bulletIndent=2)
D=json.load(open('out/rozklad_data.json'))
c=canvas.Canvas('out/raport.pdf',pagesize=(W,H))
c.setTitle('Siatka busów gminy Koszęcin – propozycja');c.setAuthor('Bartosz')
def head(title,sub=None,band=False):
    if band:
        c.setFillColor(G)
    else: c.setFillColor(INK)
    c.setFont('IB',28);c.drawString(M,H-62,title)
    if sub: c.setFont('I',13);c.setFillColor(MUT);c.drawString(M,H-88,sub)
def foot(n):
    c.setFont('I',8.5);c.setFillColor(MUT);c.drawString(M,22,'Propozycja siatki busów gminy Koszęcin · do dyskusji · 19.11.2026');c.drawRightString(W-M,22,str(n))
def flow(items,x,y,w,h):
    f=Frame(x,y,w,h,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,showBoundary=0);f.addFromList(items,c)
def B(t): return Paragraph(t,BL,bulletText='•')
page=[4]
def newpage():
    foot(page[0]);c.showPage();page[0]+=1
# ---------- Page 1: summary
head('Siatka busów gminy Koszęcin: węzeł Koszęcin Rynek','Propozycja do dyskusji · analiza dzisiejszego rozkładu GTV, nowa siatka, rozkład w takcie, kosztorys',band=True)
figs=[('4 linie','wszystkie przez Koszęcin Rynek, przesiadki 6–14 minut, przy spóźnieniu bus czeka'),('linia 1 co godzinę','kręgosłup Piasek – Strzebiń – Koszęcin – Lubliniec; linie 2, 3 i 4 to dojazdówki co 2 godziny, w szczytach szkolnych częściej'),('7 stacji','Lubliniec, Lisów, Koszęcin, Strzebiń, Rusinowice, Boronów i Kalety połączone z siecią busów'),('6+1 busów','6 przez cały dzień, 7 w szczytach; wariant oszczędny ok. 390 tys. km rocznie, pełny ok. 575 tys. km')]
x=M;y=H-110;cw=(W-2*M)/4
c.setStrokeColor(G);c.setLineWidth(2);c.line(M,H-118,W-M,H-118)
for a,b in figs:
    c.setFillColor(G);c.setFont('IB',30);c.drawString(x,y-50,a)
    p=Paragraph(b,ParagraphStyle('f',fontName='I',fontSize=12,leading=15,textColor=INK));_w,_h=p.wrapOn(c,cw-20,80);p.drawOn(c,x,y-62-_h)
    x+=cw
left=[Paragraph('Co jest dziś nie tak',H2),
B('Wszystkie linie gminne kończą się w Sadowie i są ustawione pod Lubliniec. Koszęcin jest dla nich tylko przystankiem po drodze, a nie węzłem.'),
B('Bus przez Strzebiń to tranzytowa linia Tarnowskie Góry – Lubliniec, więc przyjeżdża do Koszęcina o :02, :18 i :57. Na zmianę o 8:00 jest 58 minut za wcześnie albo 18 minut po czasie, na 14:00 przyjeżdża o 14:02.'),
B('Między 15:57 a 19:04 nie ma powrotu do Strzebinia, a po 19:04 żadnego. W sobotę 4 kursy, w niedzielę nic.'),
B('Łazy i część kursów przez Strzebiń mają busy tylko w dni nauki szkolnej.'),
B('Busy nie są zgrane z pociągami, a przy stacjach w Strzebiniu i Koszęcinie nie ma przystanków.'),
Paragraph('Co proponujemy',H2),
B('<b>Koszęcin Rynek jako główny węzeł</b> w stałym takcie co godzinę. Linia 1 przejeżdża bez czekania (w stronę Lublińca :53/:55, w stronę Strzebinia :00/:02), a pozostałe linie dowożą do niej na :49 i odjeżdżają o :03.'),
B('<b>4 linie, 6 autobusów (w szczytach 7).</b> Linia 1 przelotowa Piasek – Strzebiń – Koszęcin – Lubliniec (2 busy, co godzinę), linia 2 Boronów – Kalety, linia 3 Lisów PKP – Koszęcin PKP, linia 4 Łazy – Piłka; linie 2, 3 i 4 to dojazdówki co 2 godziny; w szczytach szkolnych linia 3 jeździ co godzinę, linia 4 w obie strony (drugi bus), a linia 2 ma dodatkowe kursy Kalety – Brusiek – Rynek. Linie 2, 3 i 4 dojeżdżają do stacji Koszęcin PKP i przystanku Koszęcin Szkoła (pociągi do Lublińca, Tarnowskich Gór, Bytomia, Katowic).'),
B('<b>Węzły na styku z sąsiadami:</b> Lubliniec PKP, Lisów PKP (przesiadka na Częstochowę), Boronów, Piasek, Kalety PKP i Brusiek (dla gminy Tworóg). Sąsiedzi dowożą do nas, my do nich, nikt nie dubluje kursów.'),
B('<b>Przystanki przy stacjach:</b> Koszęcin PKP, Boronów PKP, Kalety PKP, Lisów PKP; w Strzebiniu przystanek Strzebiń Lubliniecka obsługuje stację, a po przeniesieniu peronu pod wiadukt przystanek będzie przy nim.'),
B('<b>Psary i LO w Psarach:</b> linia 1 jedzie z Piasku najkrótszą drogą przez Płaszczymąkę (przystanek Psary Skrzyżowanie). Samo Psary obsługuje gmina Woźniki (busy GTV z Piasku do Psar i Woźnik, linia powiatowa 69 Psary – Bukowiec). Propozycje poza siatką podstawową: kursy szkolne 4S Łazy – Strzebiń – Bukowiec – Psary (19 min, zgrane z linią 1) i pętla 4P przez Łazy i Psary po utwardzeniu 1,4 km drogi w gminie Woźniki.')]
right=[Paragraph('Spis treści',H3)]+[Paragraph(t,P) for t in ['1. Schemat linii z kierunkami dalszej jazdy','2. Mapa całej siatki (trasy po drogach z OpenStreetMap)','3. Przybliżenie Koszęcin – Strzebiń','4. Podsumowanie (ta strona)','5. Dlaczego takie trasy, czy czasy są realne','6–9. Rozkład jazdy linii 1–4 (dni robocze, soboty, niedziele)','10. Przykładowe dojazdy z różnych stron gminy','11. Każda miejscowość: do Lublińca i z powrotem','12. Przesiadki na kolej','13. Zakres przewozów i porównanie z dzisiejszą siatką']]+[Spacer(1,14),Paragraph('Najważniejsze liczby',H3)]+[Paragraph(t,P) for t in ['Dziś gmina wydaje na komunikację <b>1,35 mln zł</b> rocznie (wykonanie 2024), czyli ok. 114 zł na mieszkańca.','Wariant oszczędny to ok. <b>390 tys. km</b> rocznie, niewiele więcej niż co dzisiejsze linie gminne (szacunek 300–350 tys. km), więc przy tej samej cenie za kilometr kosztowałby podobnie jak dziś. Wariant pełny to ok. <b>575 tys. km</b>. Część kilometrów leży poza gminą i może być współfinansowana przez sąsiadów.','Uwagi do planu transportowego „Jedźmy razem!” można składać <b>do 7.12.2026</b>.']]
flow(left,M,50,(W-2*M)*0.6,H-340)
flow(right,M+(W-2*M)*0.64,50,(W-2*M)*0.36,H-340)
newpage()
page[0]=5
exec(open('skrypty/raport2.py').read())
c.save()
