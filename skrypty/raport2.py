# ---------- Page 5: why routes + realism
head('Dlaczego takie trasy i czy czasy są realne')
why=[Paragraph('Dlaczego takie trasy',H2)]
txt={'1':'Linia przelotowa: ze Strzebinia do Lublińca bez przesiadki w 38 minut, bez czekania na Rynku – pozostałe linie dowożą do niej o czasie. Z Piasku najkrótszą drogą przez Płaszczymąkę (Psary obsługuje gmina Woźniki: busy GTV z Piasku, linia powiatowa 69). 2 busy, co godzinę. Przed Lublińcem 3 minuty zapasu na zamknięty przejazd kolejowy: w Lublińcu przyjazd :22, odjazd :33. W dni robocze ostatni kurs z Lublińca o 22:33 (Strzebiń Centrum 23:12).',
'2':'Oś północ–południe przez stacje Boronów, Koszęcin PKP i Kalety oraz węzeł na Rynku. W Boronowie przesiadka na Częstochowę, w Bruśku dowóz z gminy Tworóg, w Kaletach pociągi w czterech kierunkach. 2 busy, co 2 godziny w każdą stronę; do Koszęcin Szkoła z Bruśka i Kalet 7:48, z Boronowa 7:04.',
'3':'Północ gminy (Cieszowa, Hadra, Mochała, Chwostek) do Rynku i stacji Koszęcin PKP, z drugiej strony pętla przy stacji Lisów PKP – stamtąd pociąg do Częstochowy 26 minut (Lisów to gmina Herby). Co 2 godziny, w szczytach szkolnych co godzinę.',
'4':'Łazy, Stary Strzebiń i Strzebiń do Koszęcina (stacja, szkoła, Rynek). 1 bus, co godzinę. W szczytach w pulsie: z Łaz :34, Strzebiń Centrum :41 (przesiadka na linię 1 do Lublińca :44), Koszęcin PKP :54, Rynek :58; z Rynku :03 (po linii 1 z Lublińca) przez Koszęcin PKP (do :11) do Łaz :31. Poza szczytem 15 minut później, żeby nie jechać razem z linią 1: Strzebiń ma wtedy dwa różne odjazdy do Koszęcina w godzinie. Łazy → Strzebiń Szkoła 7:34 → 7:40. Propozycja 4S: kursy szkolne Łazy – Strzebiń – Bukowiec – Psary (do uzgodnienia z gminą Woźniki).',
'5':'Zachód gminy do Koszęcina i do Lublińca. Bus jedzie przez Rusinowice (z Piłki do Koszęcina prosto tylko droga pożarowa) i wjeżdża do Piłki na odnodze. Z Lublińca :05 → Sadów :15 → Piłka :27 → Wierzbie :38 → Rynek :49 → Koszęcin PKP :54; z Koszęcina PKP :06 → Rynek :11 → Piłka :33 → Sadów :45 → Lubliniec :55. Co 2 godziny, w szczytach co godzinę (2 busy). Piłka – Lubliniec 22 minuty bez przesiadki; Sadów ma do Lublińca bus co ok. pół godziny. Zastępuje propozycję 4L i osobny kurs szkolny dla Piłki.'}

for k,t in txt.items():
    why.append(Paragraph(f'<font name="IB" color="{LC[k]}">Linia {k}</font> <b>{LN[k]}</b>',ParagraphStyle('x',parent=P,spaceAfter=2)))
    why.append(Paragraph(t,ParagraphStyle('y',parent=P,fontSize=11.5,leading=16,spaceAfter=10)))
real=[Paragraph('Czas jazdy: ostrożniej niż dziś jeździ GTV',H2)]
tb=Table([['Odcinek','GTV dziś','Propozycja'],['Strzebiń → Koszęcin Rynek','6 min','8 min'],['Bukowiec → Koszęcin Rynek','12 min','13 min'],['Lubliniec → Koszęcin Rynek','14 min*','22 min']],colWidths=[230,90,90])
tb.setStyle(TableStyle([('FONT',(0,0),(-1,-1),'I',12),('FONT',(0,0),(-1,0),'IS',10.5),('TEXTCOLOR',(0,0),(-1,0),MUT),('LINEBELOW',(0,0),(-1,-1),0.6,RULE),('ALIGN',(1,0),(-1,-1),'RIGHT'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5)]))
real+=[tb,Spacer(1,6),Paragraph('Założenie: średnio 40 km/h plus 45 s na przystanek, długości tras po drogach z OpenStreetMap. Na mapie i schemacie są tylko główne przystanki; po drodze linie zatrzymują się też na mniejszych, np. Prądy na liniach 1 i 4. Busy w symulacji: do 50 km/h w terenie zabudowanym, do 70 km/h poza nim. *Dzisiejszy kurs przyspieszony bez wjazdu do Wierzbia i Irek.',PS),
Paragraph('Kierowcy: przerwy i zmiany mieszczą się w postojach',H2),
Paragraph('Wszystkie linie mają poniżej 50 km, więc obowiązują krajowe przepisy dla przewozów regularnych (ustawa o czasie pracy kierowców): przy 6–8 godzinach jazdy dziennie co najmniej 30 minut przerwy, powyżej 8 godzin 45 minut.',P),
Paragraph('W rozkładzie każdy bus ma na pętlach postój, a w ciągu dnia kilka postojów 30-minutowych i dłuższych (Lubliniec PKP, Lisów PKP, Boronów, Rynek). Busy jeżdżące od 5:30 do 22:30 obsadzają dwie zmiany kierowców, ze zmianą na pętli albo na Rynku.',P),
Paragraph('Potrzeba 7 autobusów przez cały dzień (linia 1: 2, linia 2: 2, linie 3, 4 i 5: po 1) i ósmego w szczytach (drugi bus linii 5), czyli około 15 kierowców w dzień roboczy, a z rezerwą na urlopy i weekendy około 17 etatów po stronie przewoźnika. Ten koszt jest w stawce za wozokilometr.',P),
Paragraph('Postoje dają zapas na korki i zimę: spóźnienie do kilkunastu minut nie rozbija taktu.',PS)]
flow(why,M,50,(W-2*M)*0.52,H-140)
flow(real,M+(W-2*M)*0.56,50,(W-2*M)*0.44,H-140)
newpage()
# ---------- Timetables
DAYN={'wd':'Poniedziałek – piątek','sat':'Sobota','sun':'Niedziela i święta'}
fm=lambda m:f"{(m%1440)//60}:{m%60:02d}"
def ttable(dd,maxw=640):
    tr=sorted(dd['trips'],key=lambda t:min(x for x in t[0] if x is not None))
    rows=[]
    for i,stp in enumerate(dd['stops']):
        rows.append([stp.replace(' – nowa lokalizacja',' (nowa)').replace(' (Płaszczymąka)','')]+[('–' if t[0][i] is None else fm(t[0][i])) for t in tr])
    n=len(tr);sw=150;colw=min(34,(maxw-sw-4)/max(n,1))
    if colw<32: sw=140;colw=min(34,(maxw-sw-4)/max(n,1))
    fs=9 if colw>=31 else 8.3;pd=3 if colw>=31 else 1.5
    t=Table(rows,colWidths=[sw]+[colw]*n,hAlign='LEFT')
    st=[('FONT',(0,0),(-1,-1),'I',fs),('ALIGN',(1,0),(-1,-1),'RIGHT'),('LINEBELOW',(0,0),(-1,-1),0.4,RULE),('TOPPADDING',(0,0),(-1,-1),2.5),('BOTTOMPADDING',(0,0),(-1,-1),2.5),('LEFTPADDING',(0,0),(-1,-1),pd),('RIGHTPADDING',(0,0),(-1,-1),pd)]
    ri=dd['stops'].index('Koszęcin Rynek');st+=[('BACKGROUND',(0,ri),(-1,ri),LIME),('FONT',(0,ri),(-1,ri),'IB',fs)]
    for j,t_ in enumerate(tr):
        if t_[1]: st+=[('TEXTCOLOR',(j+1,0),(j+1,-1),MUT)]
    t.setStyle(TableStyle(st));return t,all(t_[1] for t_ in tr)
for k in ['1','2','3','4','5']:
    head(f'Linia {k}',LN[k])
    c.setFillColor(colors.HexColor(LC[k]));c.roundRect(W-M-60,H-80,60,40,6,stroke=0,fill=1);c.setFillColor(colors.white);c.setFont('IB',24);c.drawCentredString(W-M-30,H-68,k)
    L=[];R=[]
    for d,target in [('wd',L),('sat',R),('sun',R)]:
        G_=D['tt'][k][d]
        for nm in list(G_):   # kursy skrócone dopisz do pełnego kierunku
            sv=G_[nm]['stops']
            for nm2,v2 in G_.items():
                S2=v2['stops']
                if nm2!=nm and len(S2)>len(sv) and S2[0]==sv[0] or (nm2!=nm and len(S2)>len(sv) and S2[-1]==sv[-1]):
                    if all(x in S2 for x in sv):
                        for t,dm in G_[nm]['trips']:
                            v2['trips'].append([[t[sv.index(x)] if x in sv else None for x in S2],dm])
                        del G_[nm];break
        for n_i,(nm,dd) in enumerate(G_.items()):
            t,alld=ttable(dd,640 if target is L else W-2*M-660)
            target.append(Paragraph(f'<b>{DAYN[d]}</b> · {nm}'+(' · <font color="#5b6b66">na zamówienie</font>' if alld else ''),ParagraphStyle('t',parent=P,fontSize=11.5,spaceBefore=8,spaceAfter=4)))
            target.append(t)
    L.append(Spacer(1,10));L.append(Paragraph('Wiersz zielony: Koszęcin Rynek, węzeł. Linia 1 przejeżdża bez czekania (:53/:55 w stronę Lublińca, :00/:02 w stronę Strzebinia), linie 2, 3 i 5 przyjeżdżają o :49, linie 2 i 3 odjeżdżają o :03, linia 5 o :11 (po postoju na Koszęcinie PKP). Linia 4 przyjeżdża o :58 i odjeżdża o :03, poza szczytem o :13 i :18. Szare godziny: kurs na zamówienie (telefon lub aplikacja). Czasy przejazdu: 40 km/h plus 45 s na przystanek.',PS))
    flow(L,M,50,640,H-150);flow(R,M+660,50,W-2*M-660,H-150)
    newpage()
# ---------- Examples
head('Przykładowe dojazdy w dzień roboczy','Godziny z proponowanego rozkładu; pociągi wg rozkładu PKP na 23.11.2026 (Koleo), po 13.12 mogą się przesunąć o kilka minut')
EXR=[['Skąd → dokąd','Jak jechać','Wyjazd','Przyjazd','Dziś'],
['Strzebiń → Koszęcin Rynek (praca na 7:00)','linia 1','6:45','6:53','na 8:00 dopiero 8:18'],
['Strzebiń → Częstochowa','linia 1, Rynek → linia 3 (6:03), Lisów PKP → KŚ 6:46','5:45','7:12','5:29 → 7:12, 2 przesiadki'],
['Koszęcin Rynek → Tarnowskie Góry','linia 1 do Strzebinia Lublinieckiej, 5 min pieszo, KŚ 7:24','7:02','7:41',''],
['Cieszowa → Koszęcin Szkoła (lekcje 8:00)','linia 3','7:42','7:50',''],
['Hadra → Tarnowskie Góry','linia 3 do Koszęcina PKP (6:54), KŚ 6:58','6:37','7:16',''],
['Piłka → Lubliniec PKP','linia 5, bez przesiadki','7:33','7:55',''],
['Sadów → Koszęcin Rynek (urząd, ośrodek zdrowia)','linia 1','7:45','8:00',''],
['Łazy → Koszęcin Rynek','linia 4, przez Koszęcin PKP','7:34','7:58','co godzinę'],
['Łazy → Strzebiń Szkoła (lekcje 8:00)','linia 4','7:34','7:40',''],
['Piłka → Rusinowice, szkoła','linia 5','7:27','7:31',''],
['Wierzbie → Sadów Szkoła','linia 5, przez Rusinowice','7:22','7:44',''],
['Irki → Koszęcin Szkoła','linia 5','6:44','6:50','albo 7:44 → 7:50'],
['Boronów → Lubliniec PKP','linia 2, Rynek → linia 1 (6:55)','6:37','7:22',''],
['Boronów → Kalety PKP','linia 2, bez przesiadki','6:37','7:30',''],
['Brusiek → Koszęcin Szkoła (lekcje 8:00)','linia 2','7:35','7:48',''],
['Kalety PKP → Koszęcin Rynek','linia 2','7:23','7:49',''],
['Łazy → Tarnowskie Góry','linia 4 do Koszęcina PKP (7:54), KŚ 8:09','7:34','8:24',''],
['Łazy → Psary, szkoła (propozycja 4S)','kurs szkolny przez Strzebiń i Bukowiec','7:09','7:29',''],
['Sadów / Koszęcin → Psary, szkoła','linia 1 do Strzebinia Centrum (7:12) → 4S 7:17','6:45 / 7:02','7:29',''],
['Psary → Koszęcin Rynek, po lekcjach','4S 13:27 / 14:27 / 15:27 → Płaszczymąka → linia 1 :37','13:27','13:53',''],
['Lubliniec PKP → Strzebiń, po zmianie do 22:00','linia 1, ostatni kurs','22:33','23:12','ostatni 19:04, w niedzielę nic']]
tex=Table(EXR,colWidths=[290,350,90,90,210])
sx=[('FONT',(0,0),(-1,-1),'I',11.5),('FONT',(0,0),(-1,0),'IS',10.5),('TEXTCOLOR',(0,0),(-1,0),MUT),('FONT',(2,1),(3,-1),'IB',12),('TEXTCOLOR',(4,1),(4,-1),MUT),('LINEBELOW',(0,0),(-1,-1),0.5,RULE),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]
for i,r_ in enumerate(EXR):
    if i and any(w in r_[0] for w in ('Częstochowa','Tarnowskie','Psary','Rusinowice','Szkoła','szkoła')): sx.append(('BACKGROUND',(0,i),(-1,i),LIME))
tex.setStyle(TableStyle(sx))
flow([tex,Spacer(1,12),Paragraph('<b>Lisów PKP jako przesiadka na Częstochowę.</b> Pociąg Kolei Śląskich z Lublińca staje w Lisowie 9 minut później i jedzie do Częstochowy 26 minut. Linia 3 kończy się przy stacji, więc dla Cieszowej, Dołów, Chwostka i Rynku to naturalna przesiadka zamiast Lublińca. Ze Strzebinia przyjazd do Częstochowy jest ten sam co przez Lubliniec, ale bilet kolejowy krótszy. <b>Propozycja 4P (na mapie kropkowana):</b> pętla Strzebiń Szkoła – Łazy – Psary – Płaszczymąka – Bukowiec – Strzebiń, 13,8 km i 25 min na kółko, Łazy → Psary 6 min; wymaga utwardzenia ok. 1,4 km drogi szutrowej Łazy – ul. Poznańska, prawie całej w gminie Woźniki (inwestycja drogowa, możliwe dofinansowanie z Rządowego Funduszu Rozwoju Dróg). <b>Propozycja 4S:</b> kursy szkolne Łazy – Strzebiń Szkoła – Strzebiń Centrum – Bukowiec – Płaszczymąka – Psary (20 min) w dni nauki; przesiadka z linii 1 w Strzebiniu Centrum z 5-minutowym zapasem (rano 7:12 → 7:17), powroty z Psar o 13:27, 14:27 i 15:27 z przesiadką na linię 1 na Płaszczymące (6 min); osobny bus lub autobus szkolny, około 8 tys. km rocznie, do podziału z gminą Woźniki.',P)],M,50,W-2*M,H-140)
newpage()
# ---------- Dojazdy do / z Lublińca (wszystkie miejscowości)
head('Każda miejscowość: rano do Lublińca, po południu z powrotem','Dzień roboczy, wariant pełny · cel: Lubliniec PKP (szkoły i zakłady w Lublińcu) · czasy z proponowanego rozkładu, z przesiadkami na Rynku lub w Strzebiniu')
AM=[['Skąd','Jak jechać','Praca na 7:00\nwyjazd → Lubliniec','Szkoła na 8:00\nwyjazd → Lubliniec'],
['Sadów','linia 1 (albo linia 5 :45 → :55)','6:10 → 6:22','7:10 → 7:22'],
['Wierzbie','linia 1','6:06 → 6:22','7:06 → 7:22'],
['Rzyce Irki','linia 1','6:00 → 6:22','7:00 → 7:22'],
['Koszęcin Rynek','linia 1','5:53 → 6:22','6:53 → 7:22'],
['Strzebiń Centrum','linia 1','5:44 → 6:22','6:44 → 7:22'],
['Bukowiec','linia 1','5:38 → 6:22','6:38 → 7:22'],
['Strzebiń Szkoła','linia 4 → w Strzebiniu linia 1','5:40 → 6:22','6:40 → 7:22'],
['Łazy','linia 4 → w Strzebiniu linia 1','5:34 → 6:22','6:34 → 7:22'],
['Cieszowa','linia 3 → na Rynku linia 1','5:42 → 6:22','6:42 → 7:22'],
['Brusiek','linia 2 → na Rynku linia 1','5:35 → 6:22','6:35 → 7:22'],
['Rusinowice','linia 5, bez przesiadki','6:38 → 6:55','7:38 → 7:55'],
['Piłka','linia 5, bez przesiadki','6:33 → 6:55','7:33 → 7:55']]
PM=[['Dokąd','Odjazd 14:33\npo lekcjach','Odjazd 15:33\nlekcje, praca','Odjazd 16:33\npo pracy'],
['Sadów / Wierzbie / Irki','14:45 / 14:49 / 14:55','15:45 / 15:49 / 15:55','16:45 / 16:49 / 16:55'],
['Koszęcin Rynek','15:00','16:00','17:00'],
['Strzebiń Centrum / Bukowiec','15:12 / 15:18','16:12 / 16:18','17:12 / 17:18'],
['Strzebiń Szkoła / Łazy','15:25 / 15:31','16:25 / 16:31','17:25 / 17:31'],
['Cieszowa','15:10','16:10','18:10'],
['Brusiek','15:17','16:17','17:17'],
['Rusinowice / Piłka*','15:22 / 15:27','16:22 / 16:27','17:22 / 17:27']]
def _tab(rows,cw,bold_from,fs=11):
    t=Table(rows,colWidths=cw)
    st=[('FONT',(0,0),(-1,-1),'I',fs),('FONT',(0,0),(-1,0),'IS',10),('TEXTCOLOR',(0,0),(-1,0),MUT),('FONT',(bold_from,1),(-1,-1),'IB',fs+0.5),('FONT',(0,1),(0,-1),'IB',fs),
        ('LINEBELOW',(0,0),(-1,-1),0.5,RULE),('TOPPADDING',(0,0),(-1,-1),4.5),('BOTTOMPADDING',(0,0),(-1,-1),4.5),('VALIGN',(0,0),(-1,-1),'MIDDLE')]
    t.setStyle(TableStyle(st));return t
tl=_tab(AM,[120,200,120,120],2);tr_=_tab(PM,[187,111,111,111],1,10)
flow([Paragraph('Rano do Lublińca',H3),tl,Spacer(1,10),Paragraph('Z każdej miejscowości gminy jest dojazd na 7:00 do pracy i na 8:00 do szkoły w Lublińcu. Linie 1 i 5 dojeżdżają bez przesiadki, z pozostałych wsi jedzie się dojazdówką z przesiadką bez czekania. W szczytach linia 2 ma dodatkowy kurs z Bruśka.',PS)],M,50,570,H-150)
flow([Paragraph('Po południu z Lublińca – o której w domu',H3),tr_,Spacer(1,10),Paragraph('Po lekcjach (kursy 14:33 i 15:33) każda miejscowość jest w domu w niecałą godzinę. Po kursie 16:33 do Cieszowej jest dalej co 2 godziny. *Do Rusinowic i Piłki wraca się bez przesiadki linią 5 z Lublińca o 15:05, 16:05 i 17:05. Do Rusinowic można też wrócić pociągiem z Lublińca.',PS),
Spacer(1,8),Paragraph('Przyjazd do Lublińca o 6:22 i 7:22 daje zapas na dojście do zakładu lub szkoły. Linia 1 jeździ co godzinę przez cały dzień, więc pozostałe godziny pracy i lekcji mają dojazd o tej samej minucie.',PS)],M+590,50,W-2*M-590,H-150)
newpage()
# ---------- Rail
head('Przesiadki na kolej w dzień roboczy','Pociągi wg rozkładu PKP na poniedziałek 23.11.2026 (Koleo). 13.12.2026 wchodzi nowy rozkład – minuty busów przy stacjach do sprawdzenia po jego publikacji')
RR=[['Stacja i kierunek','Pociągi (odjazdy)','Bus na stację','Czekanie'],
['Strzebiń → Tarnowskie Góry (17–18 min)','4:47, 5:29, 6:48, 7:24, 8:16, 9:31, 10:38, 11:21, 14:27, 16:28, 16:52, 17:47, 18:32, 20:29','linia 1 od Koszęcina, Irek, Wierzbia, Sadowa: Strzebiń Centrum :12, 5 min pieszo','6–22 min na 9 z 14 pociągów'],
['Koszęcin PKP → Tarnowskie Góry (17–18 min)','prawie co godzinę ok. :00: 5:01, 6:02, 6:58, 8:06, 8:56, 10:01, 11:01, 11:59, 15:01, 15:59, 16:58, 18:58, 19:58, 21:02, 21:56, 22:40','linia 3 z Cieszowej, Dołów, Rynku: :54; linia 4 z Łazów i Strzebinia: :54 co godzinę (poza szczytem :09); linia 5 z Piłki, Rusinowic, Wierzbia, Irek i Sadowa: :54, odjazd spod stacji :06; linia 2 od Kalet i Bruśka: :44 co 2 h','4–12 min (linie 3 i 4, ciasno przy :56–:58), 12–22 min (linia 2)'],
['Lubliniec PKP → Częstochowa, KŚ (35 min)','5:37, 6:37, 8:41, 10:51, 12:38, 15:37, 17:32, 20:54','linia 1: przyjazd :22','17–31 min'],
['Lubliniec PKP → Częstochowa, IC/EIP (27–28 min)','5:10, 7:41, 8:03, 9:52, 11:53, 15:57, 20:03','linia 1: przyjazd :22','21–43 min, osobny bilet PKP Intercity'],
['Lisów PKP → Częstochowa, KŚ (26 min)','5:46, 6:46, 8:50, 11:00, 12:47, 15:46 (te same pociągi co z Lublińca, 9 min później)','linia 3: przyjazd :24','23–37 min']]
rt=Table(RR,colWidths=[230,400,300,170])
rt.setStyle(TableStyle([('FONT',(0,0),(-1,-1),'I',11),('FONT',(0,0),(-1,0),'IS',10.5),('FONT',(0,1),(0,-1),'IB',11),('TEXTCOLOR',(0,0),(-1,0),MUT),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),0.5,RULE),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
RRP=[[Paragraph(str(c),ParagraphStyle('rr',parent=P,fontSize=10.5,leading=14,fontName='IB' if (j==0 and i>0) else ('IS' if i==0 else 'I'),textColor=MUT if i==0 else INK)) for j,c in enumerate(r)] for i,r in enumerate(RR)]
rt=Table(RRP,colWidths=[220,420,300,160]);rt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),0.5,RULE),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
flow([rt,Spacer(1,14),Paragraph('<b>Strzebiń i Koszęcin uzupełniają się w kierunku Tarnowskich Gór.</b> Ze Strzebinia jedzie 14 pociągów dziennie w nieregularnych odstępach, z Koszęcina prawie co godzinę. Mieszkańcy Koszęcina, Irek, Wierzbia i Sadowa mają dobry dojazd linią 1 na pociągi ze Strzebinia (bus o :12, pociągi zwykle :16–:32). W drugą stronę dowozi linia 4: od strony Strzebinia jedzie przez stację Koszęcin PKP (:54 w szczytach), a linia 5 dowozi na stację zachód gminy (:54) i zabiera pasażerów z pociągów (:06). Na co dzień dla Strzebinia podstawą jest jego własna stacja (bus Strzebiń Centrum lub Strzebiń Szkoła, ok. 300 m, 5 min pieszo).',P),
Paragraph('<b>Do sprawdzenia:</b> powroty z pociągu na busa (pociąg → bus), dla których tu nie zestawiono minut, oraz cały kierunek po zmianie rozkładu 13.12. Zasada: nie przestawiamy taktu pod pojedyncze pociągi, tylko sprawdzamy, które przesiadki wychodzą z ustalonego układu.',P)],M,50,W-2*M,H-140)
newpage()
# ---------- Public scope page (bez stawek)
import json as _j
_V=_j.load(open('out/rozklad_data.json'))['var']
head('Zakres przewozów i porównanie z dzisiejszą siatką','Ile kilometrów i kursów, ile busów – bez stawek; koszt zależy od ceny za kilometr w umowie z przewoźnikiem')
_LN={'1':'1 Piasek – Strzebiń – Koszęcin – Lubliniec PKP','2':'2 Boronów – Koszęcin – Brusiek – Kalety PKP','3':'3 Lisów PKP – Cieszowa – Koszęcin PKP','4':'4 Łazy – Strzebiń – Koszęcin PKP – Rynek','5':'5 Koszęcin PKP – Wierzbie – Piłka – Sadów – Lubliniec'}
_r=[['Linia','Pełny\nkursy w dzień roboczy','Pełny\ntys. km rocznie','Oszczędny\nkursy w dzień roboczy','Oszczędny\ntys. km rocznie']]
for k in '12345':
    a=_V['pelny'][0][k];b=_V['oszczedny'][0][k]
    _r.append([_LN[k],str(a['wd']['kursy']+a['wd']['zam']),f"{a['km_rok']/1000:.0f}",str(b['wd']['kursy']+b['wd']['zam']),f"{b['km_rok']/1000:.0f}"])
_r.append(['Razem (7 autobusów, w szczytach 8)','',f"{_V['pelny'][1]/1000:.0f}",'',f"{_V['oszczedny'][1]/1000:.0f}"])
_r.append(['Dziś: 5 linii gminnych (szacunek z tabliczek)','ok. 90','300–350','',''])
_t=Table(_r,colWidths=[400,150,150,170,150])
_t.setStyle(TableStyle([('FONT',(0,0),(-1,-1),'I',12),('FONT',(0,0),(-1,0),'IS',10.5),('TEXTCOLOR',(0,0),(-1,0),MUT),('FONT',(0,6),(-1,6),'IB',12.5),('BACKGROUND',(0,6),(-1,6),LIME),('TEXTCOLOR',(0,7),(-1,7),MUT),('ALIGN',(1,0),(-1,-1),'RIGHT'),('LINEBELOW',(0,0),(-1,-1),0.5,RULE),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
flow([_t,Spacer(1,16),
Paragraph('<b>Za co gmina płaci dziś.</b> Umowa gminy obejmuje pięć krótkich linii lokalnych (Koszęcin – Sadów Kopce, Strzebiń Bukowiec – Sadów Kopce, Brusiek – Sadów Kopce, Sadów – Strzebiń Bukowiec, Koszęcin – Sadów Podlesie; ogłoszenie w TED z 31.01.2025). Kursy do Tarnowskich Gór i Częstochowy, widoczne na tabliczkach w Strzebiniu i Koszęcinie, to linie przewoźnika na własny rachunek i nie wchodzą w wydatki gminy (1,35 mln zł w 2024 r.). Z tabliczek wychodzi dziś ok. 300–350 tys. km rocznie na liniach gminnych; dokładną liczbę zna gmina.',P),
Paragraph('<b>Wniosek.</b> Wariant oszczędny to ok. 510 tys. km rocznie, czyli ok. 1,5 raza więcej niż dzisiejsze linie gminne (300–350 tys.), a wariant pełny ok. 685 tys. km, około dwa razy więcej: linia 1 co godzinę od rana do 23:10, linia 4 co godzinę, wieczory i weekendy. W zamian gmina dostaje węzeł na Rynku, stały takt, dojazd do szkół i do 7 stacji kolejowych oraz bezpośredni dojazd z Piłki, Rusinowic i Sadowa do Lublińca. Część kilometrów leży poza gminą (Lubliniec, Lisów, Kalety, Boronów, Piasek) i w „Jedźmy razem!” mogą je współfinansować sąsiednie gminy.',P),
Paragraph('<b>Kursy krytyczne i na zamówienie.</b> Linia 1 to kręgosłup, zawsze według rozkładu, z ostatnim kursem z Lublińca o 22:33. Linia 4 (Łazy – Koszęcin) jeździ co godzinę jednym busem. Linie 2, 3 i 5 to dojazdówki co 2 godziny; linie 3 i 5 w szczytach co godzinę (linia 5 drugim busem), linia 2 ma w szczytach dodatkowe kursy Kalety – Brusiek – Rynek (rano 6:22 z Kalet, po południu 16:03 z Rynku). Na zamówienie: linia 3 przed południem i wieczorem oraz linie 3, 4 i 5 w weekendy i święta (w tabeli liczone jako kursy).',P),
Paragraph('<b>Poza zakresem (propozycje):</b> 4S – kursy szkolne do Psar, ok. 8 tys. km i osobny bus; 4P – pętla przez Łazy i Psary po utwardzeniu ok. 1,4 km drogi w gminie Woźniki.',P)],M,50,W-2*M,H-140)
newpage()
# ---------- Strony prywatne (kosztorys) – tylko jeśli plik istnieje lokalnie
import os as _os
if _os.path.exists('skrypty/prywatne/koszty.py'): exec(open('skrypty/prywatne/koszty.py').read())
