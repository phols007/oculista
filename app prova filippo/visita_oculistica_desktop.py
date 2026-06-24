# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
from fpdf import FPDF
import os
from datetime import date

class VisitaOculisticaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modulo Visita Oculistica")
        self.root.geometry("600x800")
        self.create_widgets()

    def create_widgets(self):
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Scroll globale con due dita su Mac o rotellina su Windows/Linux ---
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mac_mousewheel(event):
            canvas.yview_scroll(int(-1 * event.delta), "units")

        system = self.root.tk.call('tk', 'windowingsystem')
        if system == 'aqua':  # macOS
            self.root.bind_all("<MouseWheel>", _on_mac_mousewheel)
        else:  # Windows/Linux
            self.root.bind_all("<MouseWheel>", _on_mousewheel)

        # Header (spazio per intestazione)
        ttk.Label(self.scrollable_frame, text="[Spazio per intestazione dello studio]", font=("Arial", 14, "bold")).pack(pady=10)

        ttk.Label(self.scrollable_frame, text="MODULO VISITA OCULISTICA", font=("Arial", 16, "bold")).pack(pady=10)

        # DATI DEL PAZIENTE
        ttk.Label(self.scrollable_frame, text="DATI DEL PAZIENTE", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        self.entry_nome = self.make_labeled_entry("Nome e Cognome:")
        self.entry_data_nascita = self.make_labeled_entry("Data di nascita (DD/MM/YYYY):")
        
        self.sesso_var = tk.StringVar()
        frame_sesso = ttk.Frame(self.scrollable_frame)
        ttk.Label(frame_sesso, text="Sesso:").pack(side="left")
        ttk.Radiobutton(frame_sesso, text="M", variable=self.sesso_var, value="M").pack(side="left", padx=5)
        ttk.Radiobutton(frame_sesso, text="F", variable=self.sesso_var, value="F").pack(side="left", padx=5)
        frame_sesso.pack(anchor="w", padx=10, pady=5)

        self.entry_codice_fiscale = self.make_labeled_entry("Codice Fiscale:")
        self.entry_indirizzo = self.make_labeled_entry("Indirizzo:")
        self.entry_telefono = self.make_labeled_entry("Telefono:")
        self.entry_email = self.make_labeled_entry("Email:")

        # MOTIVO DELLA VISITA
        ttk.Label(self.scrollable_frame, text="MOTIVO DELLA VISITA", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
        self.motivo_controllo = tk.BooleanVar()
        self.motivo_disturbi = tk.BooleanVar()
        self.motivo_prescrizione = tk.BooleanVar()
        self.motivo_altro = tk.BooleanVar()

        ttk.Checkbutton(self.scrollable_frame, text="Visita di controllo", variable=self.motivo_controllo).pack(anchor="w", padx=20)
        frame_disturbi = ttk.Frame(self.scrollable_frame)
        ttk.Checkbutton(frame_disturbi, text="Disturbi visivi", variable=self.motivo_disturbi).pack(side="left", anchor="w")
        self.entry_disturbi = ttk.Entry(frame_disturbi, width=40)
        self.entry_disturbi.pack(side="left", padx=5)
        frame_disturbi.pack(anchor="w", padx=20)

        ttk.Checkbutton(self.scrollable_frame, text="Prescrizione occhiali/lenti", variable=self.motivo_prescrizione).pack(anchor="w", padx=20)
        frame_altro = ttk.Frame(self.scrollable_frame)
        ttk.Checkbutton(frame_altro, text="Altro", variable=self.motivo_altro).pack(side="left", anchor="w")
        self.entry_altro = ttk.Entry(frame_altro, width=40)
        self.entry_altro.pack(side="left", padx=5)
        frame_altro.pack(anchor="w", padx=20)

        # ANAMNESI OCULARE E GENERALE
        ttk.Label(self.scrollable_frame, text="ANAMNESI OCULARE E GENERALE", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

        self.anamnesi_problemi_occhi = tk.StringVar(value="No")
        frame_problemi_occhi = ttk.Frame(self.scrollable_frame)
        ttk.Label(frame_problemi_occhi, text="Ha mai avuto problemi agli occhi?").pack(side="left")
        ttk.Radiobutton(frame_problemi_occhi, text="Sì", variable=self.anamnesi_problemi_occhi, value="Sì").pack(side="left", padx=5)
        ttk.Radiobutton(frame_problemi_occhi, text="No", variable=self.anamnesi_problemi_occhi, value="No").pack(side="left", padx=5)
        frame_problemi_occhi.pack(anchor="w", padx=20, pady=5)

        self.entry_problemi_occhi = self.make_labeled_entry("Se sì, quali?", parent=self.scrollable_frame, padding=(30,0,10,5))

        self.anamnesi_occhiali_lenti = tk.StringVar(value="No")
        frame_occhiali = ttk.Frame(self.scrollable_frame)
        ttk.Label(frame_occhiali, text="Porta occhiali o lenti a contatto?").pack(side="left")
        ttk.Radiobutton(frame_occhiali, text="Sì", variable=self.anamnesi_occhiali_lenti, value="Sì").pack(side="left", padx=5)
        ttk.Radiobutton(frame_occhiali, text="No", variable=self.anamnesi_occhiali_lenti, value="No").pack(side="left", padx=5)
        frame_occhiali.pack(anchor="w", padx=20, pady=5)

        self.entry_da_quanto = self.make_labeled_entry("Da quanto tempo?", parent=self.scrollable_frame, padding=(30,0,10,5))

        self.entry_malattie = self.make_labeled_entry("Malattie sistemiche (es. diabete, ipertensione):")
        self.entry_farmaci = self.make_labeled_entry("Farmaci assunti:")
        self.entry_interventi = self.make_labeled_entry("Interventi oculari pregressi:")

        # ESAME OBIETTIVO OCULARE
        ttk.Label(self.scrollable_frame, text="ESAME OBIETTIVO OCULARE", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)

        ttk.Label(self.scrollable_frame, text="Esame Annessi e Segmento Anteriore:").pack(anchor="w", padx=20)
        self.text_annessi = tk.Text(self.scrollable_frame, height=4, width=60)
        self.text_annessi.pack(padx=20, pady=5)

        self.entry_acuita_lontano_od = self.make_labeled_entry("Acuità Visiva per Lontano OD:")
        self.entry_acuita_lontano_os = self.make_labeled_entry("Acuità Visiva per Lontano OS:")

        self.entry_acuita_vicino_od = self.make_labeled_entry("Acuità Visiva per Vicino OD:")
        self.entry_acuita_vicino_os = self.make_labeled_entry("Acuità Visiva per Vicino OS:")

        ttk.Label(self.scrollable_frame, text="Refrazione OD:").pack(anchor="w", padx=20)
        self.entry_sph_od = self.make_labeled_entry("Sph:")
        self.entry_cyl_od = self.make_labeled_entry("Cyl:")
        self.entry_asse_od = self.make_labeled_entry("Asse:")

        ttk.Label(self.scrollable_frame, text="Refrazione OS:").pack(anchor="w", padx=20)
        self.entry_sph_os = self.make_labeled_entry("Sph:")
        self.entry_cyl_os = self.make_labeled_entry("Cyl:")
        self.entry_asse_os = self.make_labeled_entry("Asse:")

        self.entry_pressione_od = self.make_labeled_entry("Pressione Intraoculare OD (mmHg):")
        self.entry_pressione_os = self.make_labeled_entry("Pressione Intraoculare OS (mmHg):")

        ttk.Label(self.scrollable_frame, text="Esame del Fondo Oculare:").pack(anchor="w", padx=20)
        self.text_fondo = tk.Text(self.scrollable_frame, height=4, width=60)
        self.text_fondo.pack(padx=20, pady=5)

        ttk.Label(self.scrollable_frame, text="Altri Esami:").pack(anchor="w", padx=20)
        self.text_altri_esami = tk.Text(self.scrollable_frame, height=3, width=60)
        self.text_altri_esami.pack(padx=20, pady=5)

        # DIAGNOSI E PRESCRIZIONE
        ttk.Label(self.scrollable_frame, text="DIAGNOSI E PRESCRIZIONE", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
        self.text_diagnosi = tk.Text(self.scrollable_frame, height=4, width=60)
        self.text_diagnosi.pack(padx=20, pady=5)

        # Pulsante Genera PDF
        ttk.Button(self.scrollable_frame, text="Genera PDF", command=self.genera_pdf).pack(pady=20)

    def make_labeled_entry(self, label, parent=None, padding=(10,5,10,5)):
        if parent is None:
            parent = self.scrollable_frame
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=padding[0], pady=padding[1])
        ttk.Label(frame, text=label).pack(side="left")
        entry = ttk.Entry(frame, width=50)
        entry.pack(side="left", padx=5)
        return entry

    def genera_pdf(self):
        # Raccolta dati
        nome = self.entry_nome.get()
        data_nascita = self.entry_data_nascita.get()
        sesso = self.sesso_var.get()
        codice_fiscale = self.entry_codice_fiscale.get()
        indirizzo = self.entry_indirizzo.get()
        telefono = self.entry_telefono.get()
        email = self.entry_email.get()

        motivo = []
        if self.motivo_controllo.get(): motivo.append("Visita di controllo")
        if self.motivo_disturbi.get():
            disturbi = self.entry_disturbi.get().strip()
            motivo.append(f"Disturbi visivi ({disturbi})" if disturbi else "Disturbi visivi")
        if self.motivo_prescrizione.get(): motivo.append("Prescrizione occhiali/lenti")
        if self.motivo_altro.get():
            altro = self.entry_altro.get().strip()
            motivo.append(f"Altro ({altro})" if altro else "Altro")

        anamnesi_problemi = self.anamnesi_problemi_occhi.get()
        quali_problemi = self.entry_problemi_occhi.get()
        porta_occhiali = self.anamnesi_occhiali_lenti.get()
        da_quanto = self.entry_da_quanto.get()
        malattie = self.entry_malattie.get()
        farmaci = self.entry_farmaci.get()
        interventi = self.entry_interventi.get()

        annessi = self.text_annessi.get("1.0", "end").strip()
        acuita_lontano_od = self.entry_acuita_lontano_od.get()
        acuita_lontano_os = self.entry_acuita_lontano_os.get()
        acuita_vicino_od = self.entry_acuita_vicino_od.get()
        acuita_vicino_os = self.entry_acuita_vicino_os.get()
        sph_od = self.entry_sph_od.get()
        cyl_od = self.entry_cyl_od.get()
        asse_od = self.entry_asse_od.get()
        sph_os = self.entry_sph_os.get()
        cyl_os = self.entry_cyl_os.get()
        asse_os = self.entry_asse_os.get()
        pressione_od = self.entry_pressione_od.get()
        pressione_os = self.entry_pressione_os.get()
        fondo = self.text_fondo.get("1.0", "end").strip()
        altri_esami = self.text_altri_esami.get("1.0", "end").strip()
        diagnosi = self.text_diagnosi.get("1.0", "end").strip()

        if not nome or not data_nascita:
            messagebox.showerror("Errore", "Compila almeno Nome e Data di nascita.")
            return

        # Creazione PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Modulo Visita Oculistica", ln=True, align="C")
        pdf.ln(10)

        def write_section(title, text):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_font("Arial", "", 12)
            if isinstance(text, list):
                for line in text:
                    pdf.multi_cell(0, 8, line)
            else:
                pdf.multi_cell(0, 8, text)
            pdf.ln(5)

        write_section("DATI DEL PAZIENTE", [
            f"Nome e Cognome: {nome}",
            f"Data di nascita: {data_nascita}",
            f"Sesso: {sesso}",
            f"Codice Fiscale: {codice_fiscale}",
            f"Indirizzo: {indirizzo}",
            f"Telefono: {telefono}",
            f"Email: {email}"
        ])

        write_section("MOTIVO DELLA VISITA", motivo if motivo else "Non specificato")

        write_section("ANAMNESI OCULARE E GENERALE", [
            f"Ha mai avuto problemi agli occhi?: {anamnesi_problemi}",
            f"Se sì, quali?: {quali_problemi}",
            f"Porta occhiali o lenti a contatto?: {porta_occhiali}",
            f"Da quanto tempo?: {da_quanto}",
            f"Malattie sistemiche: {malattie}",
            f"Farmaci assunti: {farmaci}",
            f"Interventi oculari pregressi: {interventi}"
        ])

        write_section("ESAME OBIETTIVO OCULARE", [
            f"Esame Annessi e Segmento Anteriore:\n{annessi}",
            f"Acuità Visiva per Lontano OD: {acuita_lontano_od}",
            f"Acuità Visiva per Lontano OS: {acuita_lontano_os}",
            f"Acuità Visiva per Vicino OD: {acuita_vicino_od}",
            f"Acuità Visiva per Vicino OS: {acuita_vicino_os}",
            f"Refrazione OD: Sph {sph_od} Cyl {cyl_od} Asse {asse_od}",
            f"Refrazione OS: Sph {sph_os} Cyl {cyl_os} Asse {asse_os}",
            f"Pressione Intraoculare OD: {pressione_od} mmHg",
            f"Pressione Intraoculare OS: {pressione_os} mmHg",
            f"Esame del Fondo Oculare:\n{fondo}",
            f"Altri Esami:\n{altri_esami}"
        ])

        write_section("DIAGNOSI E PRESCRIZIONE", diagnosi)

        nome_file = f"{nome.replace(' ', '_')}_{date.today()}.pdf"
        cartella_destinazione = os.path.expanduser("~/Desktop/RefertiOculistici")
        os.makedirs(cartella_destinazione, exist_ok=True)
        percorso_file = os.path.join(cartella_destinazione, nome_file)
        pdf.output(percorso_file)

        messagebox.showinfo("Successo", f"PDF salvato in:\n{percorso_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisitaOculisticaApp(root)
    root.mainloop()