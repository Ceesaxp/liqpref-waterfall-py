import tkinter as tk
from tkinter import filedialog, messagebox
import plotly.graph_objects as go
import os
import csv
import sys
import locale
from PIL import Image, ImageTk
import io

GUIDE_TEXT = """\
🧠 LPW – Liquidation Preference Waterfall

📄 How the program works

This tool calculates the return for investors in liquidation preference scenarios,
both in point and iterative modes. The program uses .csv files that represent the
structure of investment rounds and allows two types of analysis:

🎯 Available modes:

1. Single file:
   Calculates the result for investors based on a single capitalization scenario.

2. Scenario comparison (two files):
   Compares two distinct scenarios by loading two separate .csv files.

3. Point EXIT calculation:
   Enter a specific EXIT value and calculate how much investors would receive in each scenario.

4. Iterative graph:
   Calculates for 100 iterations the return to investors by varying the EXIT from a chosen minimum to maximum,
   and creates a graph to observe the trend of MoIC and received EXIT.

📁 .csv file requirements

- UTF-8 format delimited by semicolon (;)
- No special characters or Excel formulas in the file
- Clean the file from empty cells or hidden formulas ("Delete" on Excel rows/columns near the data)
- Number format:
  - Integers: 1, 0, 4 (without decimals)
  - Float: 1,000,000.00 or 1000000.00

📑 .csv file template

Required fields (in order):

- Seniority: int
  Liquidation order. 1 = highest priority

- Round_Amount: float
  Total value invested for that share class

- Investor_Amount: float
  Like Round_Amount but investor's investment share

- Round_Shares: float
  Total shares assigned to the category

- Investor_Shares: float
  Like Round_Shares but for investor shares

- Preferred: int (0 or 1)
  1 = Preferred, 0 = Common

- Participating: int (0 or 1)
  1 = Participating, 0 = Non participating

- CAP: float
  Maximum CAP (e.g., 3.0 for 3x) – 0 if not present

- MP: float
  Investment multiplier – typically 1 (also for common shares)

- Common_Pool: int (0 or 1)
  1 = the category participates in the final distribution of the remainder with all others (final waterfall),
  0 = the category is excluded from this phase. Useful for managing participating preferred cases with CAP.

🔁 Note on the Common_Pool field:
Used to indicate if a category also participates in the **final and residual** distribution of the EXIT,
after the liquidation preferences have been satisfied, thus after receiving the greater value between:
    - Conversion to common
    - MP * Invested Amount
This is a special case specified in some contracts, normally it's not like this.

🛠 Common error resolution:

- Check that the file is .csv UTF-8 delimited by ;
- Remove empty cells and hidden formulas in Excel
- Verify the data format:
  • Integers → numbers like 1 or 0
  • Float → 1,000,000.00 or 1000000.00 (the program interprets them correctly)

"""


# Global variables to hold CSV records:
records1 = []  # Scenario 1
records2 = []  # Scenario 2 (optional)

# Global variable to manage the Stop button.
stop_flag = False


# Set the locale format
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')

def format_exit_value(event, entry_widget):
    try:
        text = entry_widget.get()

        # Remove previous formatting (commas)
        clean_text = text.replace(',', '')

        # Convert to float and reformat
        number = float(clean_text)
        formatted_text = "{:,.2f}".format(number)

        # Update field
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, formatted_text)

    except ValueError:
        pass  # Ignore if invalid input (non-numeric)

# === Function to parse float values ===
def parse_float(s):
    return float(str(s).replace(',', ''))  # from "1,000,000.00" → "1000000.00"


'''
def mostra_grafico_in_tk(fig):
    img_bytes = fig.to_image(format="png")  # ← usa kaleido
    image = Image.open(io.BytesIO(img_bytes))

    win = tk.Toplevel()
    win.title("Grafico Investor")
    canvas = tk.Canvas(win, width=image.width, height=image.height)
    canvas.pack()
    tk_img = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor='nw', image=tk_img)
    canvas.image = tk_img  # evita che l'immagine venga garbage collected
'''

# === Function to read CSV ===
def read_csv(filepath):
    with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        header = next(reader)  # Legge l'intestazione
        recs = []
        for row in reader:
            # Salta le righe incomplete (ci aspettiamo almeno 9 colonne)
            if len(row) < 9:
                continue
            rec = {
                "Seniority": int(row[0]),
                "Round_Amount": parse_float(row[1]),
                "Investor_Amount": parse_float(row[2]),
                "Round_Shares": parse_float(row[3]),
                "Investor_Shares": parse_float(row[4]),
                "Preferred": int(row[5]),
                "Participating": int(row[6]),
                "CAP": parse_float(row[7]),
                "mp": parse_float(row[8]),
                "Common_Pool":int(row[9]),
                "Convert": 0, # These are values that will be updated dynamically
                "MP_amount": 0,
                "Y_common": 0,
                "Y_participating": 0,
                "Residual_participation": 0,
                "EXIT_category": 0,
                "EXIT_category_investor": 0,
                "assigned": 0,
                "Residual_EXIT_turn": 0
            }
            recs.append(rec)
    return recs

# === Functions to load CSV files for Scenario 1 and Scenario 2 ===
def load_csv1():
    global records1
    filepath = filedialog.askopenfilename(
        title="Load CSV for Scenario 1",
        filetypes=[("CSV Files", "*.csv")]
    )
    if filepath:
        if not filepath.lower().endswith(".csv"):
            messagebox.showerror("Error", "The selected file is not a CSV.")
            return
        try:
            records1 = read_csv(filepath)
            label_file1.config(text=f"Scenario 1: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading file:\n{e}")

def load_csv2():
    global records2
    filepath = filedialog.askopenfilename(
        title="Load CSV for Scenario 2",
        filetypes=[("CSV Files", "*.csv")]
    )
    if filepath:
        if not filepath.lower().endswith(".csv"):
            messagebox.showerror("Error", "The selected file is not a CSV.")
            return
        try:
            records2 = read_csv(filepath)
            label_file2.config(text=f"Scenario 2: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading file:\n{e}")

# === Waterfall model simulation function (algorithm unchanged) ===

# WATERFALL LOGIC:
# Non-preferred -> always treated at the end as common
# Preferred non-participating -> they either take the invested amount or convert
# Preferred participating without cap -> mp*amount immediately then final pool with common
# Preferred participating with cap -> mp*amount immediately then final pool, check if CAP exceeded


def run_waterfall(records, EXIT_input):

    # Reset initial values
    for record in records:
        record["Convert"] = 0
        record["MP_amount"] = 0
        record["Y_common"] = 0
        record["Y_participating"] = 0
        record["Residual_participation"] = 0
        record["EXIT_category"] = 0
        record["EXIT_category_investor"] = 0
        record["assigned"] = 0
        record["Residual_EXIT_turn"] = 0

    N_TOT = sum(record["Round_Shares"] for record in records) # Total shares needed to calculate conversion to common
    EXIT_INVESTOR = 0 # This value will be updated at each waterfall step to track investor's portion
    N_Common = 0
    N_Common_Investor = 0
    Investor_Invested = sum(record["Investor_Amount"] for record in records)
    #print(Investor_Invested)


    records_sorted = sorted(records, key=lambda x: x["Seniority"])


    EXIT = EXIT_input
    for record in records_sorted:

        print(record["Seniority"])
        if record["Preferred"] == 1:
            if record["Participating"] == 0:
                #alfa = record["Round_Shares"] / N_TOT
                record["Y_common"] = (record["Round_Shares"] / N_TOT) * EXIT
                record["Y_preferred"] = record["mp"]*record["Round_Amount"]
                #Y_Preferred_Investor = Y_Preferred*(record["Investor_Amount"]/record["Round_Amount"])
                record["EXIT_category"] = max(record["Y_common"], record["Y_preferred"])
                record["EXIT_category_investor"] = record["EXIT_category"]*(record["Investor_Shares"]/record["Round_Shares"])
                if EXIT < record["EXIT_category"]:
                    print("No more availability, finishing distribution")
                    #if EXIT < record["Y_preferred"]:
                        #record["EXIT_category"] = EXIT
                        #record["EXIT_category_investor"] = record["EXIT_category"]*(record["Investor_Amount"]/record["Round_Amount"])
                    #else:
                    record["EXIT_category"] = EXIT
                    record["EXIT_category_investor"] = record["EXIT_category"] *record["Investor_Shares"]/record["Round_Shares"]

                # Assign them so they can be removed from total
                record["assigned"] = 1
                EXIT -= record["EXIT_category"]
                #print(record["EXIT_category"])
                #print("remaining:")
                #print(EXIT)
                N_TOT -= record["Round_Shares"]

            if record["Participating"] == 1:
                #record["Residuo_EXIT_turno"] = EXIT
                #alfa = record["Round_Shares"] / N_TOT
                record["Y_common"] = (record["Round_Shares"] / N_TOT) * EXIT
                record["MP_amount"] = record["mp"]*record["Round_Amount"]
                #Y_Preferred_Investor = Y_Preferred*(record["Investor_Amount"]/record["Round_Amount"])
                if EXIT <= record["MP_amount"]: # Assign immediately, no point continuing if EXIT value is exhausted
                        print("Exit value does not exceed mp*amount")
                        record["EXIT_category"] = EXIT
                        record["EXIT_category_investor"] =  record["EXIT_category"]*(record["Investor_Shares"]/record["Round_Shares"])
                        record["assigned"] = 1
                        EXIT -= record["EXIT_category"]
                        N_TOT -= record["Round_Shares"]

                else: # If available exit value exceeds what they would take as preferred, continue calculations
                    print("Still have exit available")
                    if record["CAP"] == 0: # participating without CAP
                        record["EXIT_category"] = record["MP_amount"]
                        record["EXIT_category_investor"] = record["EXIT_category"]*(record["Investor_Shares"]/record["Round_Shares"])
                        #print(record["EXIT_category"])
                        EXIT -= record["EXIT_category"]
                        # still need to assign the rest
                    if record["CAP"] > 0: # has CAP
                        if (record["CAP"]*record["Round_Amount"]) <= record["Y_common"]: # If converting immediately yields more than CAP*Amount, better to convert
                            print("Better to convert")
                            record["EXIT_category"] = record["Y_common"] # Assign converted value
                            #print(record["EXIT_category"])
                            record["EXIT_category_investor"] = record["EXIT_category"] *record["Investor_Shares"]/record["Round_Shares"]
                            record["assigned"] = 1
                            EXIT -= record["EXIT_category"]
                            N_TOT -= record["Round_Shares"]

                        elif record["CAP"]*record["Round_Amount"] > record["Y_common"]: # Otherwise assign mp*Amount and wait for participating portion
                            print("Have a preferred participating")
                            record["EXIT_category"] = record["MP_amount"]
                            record["EXIT_category_investor"] = record["EXIT_category"] *(record["Investor_Shares"]/record["Round_Shares"])
                            EXIT -= record["EXIT_category"] # Remove it because it's as if that part has already been assigned


    # Handle participating shares distribution

    print("Now assigning participating portion")
    for record in records_sorted: # Iterate over all remaining
        #print(record["Seniority"])
        if record["assigned"] == 0: # Look only at those not yet assigned
            #record["residual_participation"] = EXIT* (record["Round_Shares"] / N_TOT)
           # print("Not yet assigned")
            prev_value = record["EXIT_category"]
            if record["Preferred"] == 1 and record["Participating"] == 1 and record["CAP"] > 0: # If it's a preferred participating
                print("It's participating, participating portion")
                #prev_value = record["EXIT_category"]
                # has cap
                print("Has CAP")
                print("Previous category value")
                print(record["EXIT_category"])
                participation = EXIT * (record["Round_Shares"] / N_TOT)
                total_exit = record["MP_amount"] + participation
                #record["EXIT_category"] = record["MP_amount"] + (EXIT * (record["Round_Shares"] / N_TOT))
                #record["EXIT_category_investor"] = record["EXIT_category"]*(record["Investor_Shares"]/record["Round_Shares"])

                if total_exit > (record["CAP"]*record["Round_Amount"]): # Exceed the cap?
                        total_exit = record["CAP"]*record["Round_Amount"]
                        #record["EXIT_category"] = record["CAP"]*record["Round_Amount"] # cut at cap
                        #record["EXIT_category_investor"] = record["EXIT_category"]*(record["Investor_Amount"]/record["Round_Amount"]) # to check

                extra_assigned = total_exit - record["EXIT_category"]
                record["EXIT_category"] = total_exit
                record["EXIT_category_investor"] = record["EXIT_category"]*(record["Investor_Shares"]/record["Round_Shares"])
                #new_value = record["EXIT_category"]- prev_value
                print("Subsequent category value")
                print(record["EXIT_category"])

                EXIT -= extra_assigned
                N_TOT -= record["Round_Shares"]
                record["assigned"] = 1



    print("Now assigning participating portion")
    for record in records_sorted: # Iterate over all remaining
        print(record["Seniority"])
        if record["assigned"] == 0: # Look only at those not yet assigned
            #record["residual_participation"] = EXIT* (record["Round_Shares"] / N_TOT)
            print("Not yet assigned")
            if record["Preferred"] == 1 and record["Participating"] == 1: # If it's a preferred participating
                print("It's participating, participating portion")
                #prev_value = record["EXIT_category"]
                if record["CAP"] == 0: # Without cap -> simply assign new value portion equal to participation to existing amount
                    print("It's participating without cap")
                    print()
                    record["EXIT_category"] += (EXIT* (record["Round_Shares"] / N_TOT))
                    record["EXIT_category_investor"] = record["EXIT_category"]*record["Investor_Shares"]/record["Round_Shares"]
                    EXIT -= (EXIT* (record["Round_Shares"] / N_TOT))
                    N_TOT -= record["Round_Shares"]
                    record["assigned"] = 1

            if record["Preferred"] == 0:
                print(N_TOT)
                print(EXIT)
                record["EXIT_category"] = (EXIT* (record["Round_Shares"] / N_TOT))
                record["EXIT_category_investor"] = (record["EXIT_category"]*(record["Investor_Shares"]/record["Round_Shares"]))
                EXIT -= record["EXIT_category"]
                print("Finished")
                print(EXIT)
                print(record["EXIT_category_investor"])
                N_TOT -= record["Round_Shares"]
                record["assigned"] = 1



# Used only to calculate totals at the end
    for record in records_sorted:
        print(record["Seniority"])
        print(record["assigned"])
        print(record["EXIT_category"])
        print("Found it")
        print(record["EXIT_category_investor"])
        EXIT_INVESTOR += record["EXIT_category_investor"]
    if Investor_Invested > 0:
        MoIC = EXIT_INVESTOR/Investor_Invested
    else:
        MoIC = 0

    return EXIT_INVESTOR, MoIC





# === Function to stop calculation (Stop button) ===
def stop_calculation():
    global stop_flag
    stop_flag = True

def reset_app():
    global records1, records2, stop_flag
    stop_flag = False
    records1 = []
    records2 = []

    # Reset file labels
    label_file1.config(text="No file loaded for Scenario 1")
    label_file2.config(text="(Optional) No file loaded for Scenario 2")

    # Clear EXIT fields
    entry_single.delete(0, tk.END)
    entry_min.delete(0, tk.END)
    entry_max.delete(0, tk.END)

    # Reset to point calculation view as default
    mode_var.set(1)
    update_mode()

def show_guide():
    guide = tk.Toplevel(root)
    guide.title("Guide - LPW")
    guide.geometry("700x500")
    text = tk.Text(guide, wrap="word")
    text.insert("1.0", GUIDE_TEXT)
    text.pack(expand=True, fill="both")
    text.config(state="disabled")

# === Function for calculation based on combinations ===
def calculate():
    global stop_flag
    stop_flag = False  # Reset flag at the beginning
    # Verify that at least one file has been loaded
    if not records1 and not records2:
        messagebox.showerror("Error", "Load at least one CSV file (Scenario 1 or Scenario 2).")
        return

    mode = mode_var.get()  # 1 = Point Calculation, 2 = Iterative Graph
    if mode == 1:  # Point Calculation Mode
        try:
            exit_value = float(parse_float(entry_single.get()))
        except ValueError:
            messagebox.showerror("Error", "Enter a valid numeric value for EXIT.")
            return
        results = ""
        if records1:
            res1, MoIC1 = run_waterfall(records1, exit_value)
            res1_str = f"{res1:,.0f}".replace(",", ".")
            results += f"Scenario 1: Investor EXIT = {res1_str} €\n"
            results += f"Scenario 1: Investor MoIC = {MoIC1:,.3f}\n"
        if records2:
            res2, MoIC2 = run_waterfall(records2, exit_value)
            res2_str = f"{res2:,.0f}".replace(",", ".")
            results += f"Scenario 2: Investor EXIT = {res2_str} €\n"
            results += f"Scenario 2: Investor MoIC = {MoIC2:,.3f}\n"
        messagebox.showinfo("Result", results)
    elif mode == 2:  # Iterative Graph Mode
        try:
            exit_min = float(parse_float(entry_min.get()))
            exit_max = float(parse_float(entry_max.get()))
        except ValueError:
            messagebox.showerror("Error", "Enter valid numeric values for EXIT Min and EXIT Max.")
            return
        if exit_min >= exit_max:
            messagebox.showerror("Error", "EXIT Min must be less than EXIT Max.")
            return

        iterations = 100
        step = (exit_max - exit_min) / iterations
        exit_vals = []
        investor_vals_1 = []
        moic_vals_1 = []
        investor_vals_2 = []
        moic_vals_2 = []
        curr = exit_min
        while curr <= exit_max:
            if stop_flag:
                messagebox.showinfo("Interrupted", "The iterative calculation was interrupted.")
                break
            exit_vals.append(curr)
            if records1:
                res1, MoIC1 = run_waterfall(records1, curr)
                investor_vals_1.append(res1)
                moic_vals_1.append(MoIC1)
            else:
                investor_vals_1.append(None)
                moic_vals_1.append(None)
            if records2:
                res2, MoIC2 = run_waterfall(records2, curr)
                investor_vals_2.append(res2)
                moic_vals_2.append(MoIC2)
            else:
                investor_vals_2.append(None)
                moic_vals_2.append(None)
            curr += step

        from plotly.subplots import make_subplots

        fig = make_subplots(rows=2, cols=1, shared_xaxes=False,
                            vertical_spacing=0.15,
                            subplot_titles=("Investor EXIT vs Total EXIT", "MoIC vs Total EXIT"))

        if records1:
            fig.add_trace(go.Scatter(
                x=exit_vals,
                y=investor_vals_1,
                mode='lines+markers',
                name='Scenario 1 Investor EXIT',
                line=dict(color='royalblue', width=2),
                marker=dict(size=4)
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=exit_vals,
                y=moic_vals_1,
                mode='lines+markers',
                name='Scenario 1 MoIC',
                line=dict(color='royalblue', width=2),
                marker=dict(size=4)
            ), row=2, col=1)
        if records2:
            fig.add_trace(go.Scatter(
                x=exit_vals,
                y=investor_vals_2,
                mode='lines+markers',
                name='Scenario 2 Investor EXIT',
                line=dict(color='firebrick', width=2),
                marker=dict(size=4)
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=exit_vals,
                y=moic_vals_2,
                mode='lines+markers',
                name='Scenario 2 MoIC',
                line=dict(color='firebrick', width=2),
                marker=dict(size=4)
            ), row=2, col=1)

        # Add target line for MoIC (target = 3)
        fig.add_shape(
            type="line",
            x0=min(exit_vals),
            x1=max(exit_vals),
            y0=3,
            y1=3,
            line=dict(color="green", dash="dash", width=2),
            xref="x",
            yref="y2"  # References the Y axis of the second subplot
        )

        fig.update_layout(
        title="Comparison: Investor EXIT and MoIC vs Total EXIT",
        template="plotly_white",
        hovermode="x unified",
        width=1100,
        height=800,
        xaxis=dict(title="Total EXIT (€)"),
        yaxis=dict(title="Investor EXIT (€)"),
        xaxis2=dict(title="Total EXIT (€)"),
        yaxis2=dict(title="MoIC (x)"),
        )
        fig.update_xaxes(tickformat=",.0f", row=1, col=1)
        fig.update_xaxes(tickformat=",.0f", row=2, col=1)
        fig.update_yaxes(tickformat=",.0f", row=1, col=1)
        fig.update_yaxes(tickformat=",.3f", row=2, col=1)
        fig.show()
        # show_graph_in_tk(fig)

    else:
        messagebox.showerror("Error", "Select a valid calculation mode.")

# === Function to update interface based on selected mode ===
def update_mode():
    mode = mode_var.get()
    if mode == 1:
        frame_single.pack(pady=10, fill='x')
        frame_graph.pack_forget()
    elif mode == 2:
        frame_graph.pack(pady=10, fill='x')
        frame_single.pack_forget()



# ==== GUI Construction ====

root = tk.Tk()
root.title("Liquidation Preference Waterfall")
root.geometry("900x400")  # Window size
#root.iconbitmap("LPW_1.0.1.ico")

# Correct path to load icon even from executable
if hasattr(sys, "_MEIPASS"):
    icon_path = os.path.join(sys._MEIPASS, "LPW_1.0.1.ico")
else:
    icon_path = "LPW_1.0.1.ico"

root.iconbitmap(icon_path)

#root.iconbitmap(icon_path)
# Frame for loading CSV files
frame_file = tk.Frame(root, padx=10, pady=10)
frame_file.pack(fill='x')
btn_load1 = tk.Button(frame_file, text="Load CSV Scenario 1...", command=load_csv1)
btn_load1.pack(side='left')
label_file1 = tk.Label(frame_file, text="No file loaded for Scenario 1")
label_file1.pack(side='left', padx=10)
btn_load2 = tk.Button(frame_file, text="Load CSV Scenario 2...", command=load_csv2)
btn_load2.pack(side='left', padx=(20,0))
label_file2 = tk.Label(frame_file, text="(Optional) No file loaded for Scenario 2")
label_file2.pack(side='left', padx=10)

# Frame for choosing calculation mode (Radio Buttons)
frame_mode = tk.Frame(root, padx=10, pady=10)
frame_mode.pack(fill='x')
mode_var = tk.IntVar(value=1)
tk.Label(frame_mode, text="Calculation mode:").pack(side='left')
radio_point = tk.Radiobutton(frame_mode, text="Point calculation", variable=mode_var, value=1, command=update_mode)
radio_point.pack(side='left', padx=10)
radio_graph = tk.Radiobutton(frame_mode, text="Iterative graph", variable=mode_var, value=2, command=update_mode)
radio_graph.pack(side='left', padx=10)

#
# Frame for point calculation (single EXIT value)
frame_single = tk.Frame(root, padx=10, pady=10)
frame_single.pack(fill='x')
tk.Label(frame_single, text="Enter EXIT value (€):").pack(side='left')

entry_single = tk.Entry(frame_single)
entry_single.pack(side='left', padx=5)

# 🔁 Connect function to field to format while typing
entry_single.bind("<FocusOut>", lambda event: format_exit_value(event, entry_single))
#

# Frame per il grafico iterativo (campi EXIT Min e EXIT Max)
'''frame_graph = tk.Frame(root, padx=10, pady=10)
tk.Label(frame_graph, text="EXIT Min (€):").grid(row=0, column=0, padx=5, pady=5)
entry_min = tk.Entry(frame_graph)
entry_min.grid(row=0, column=1, padx=5, pady=5)
tk.Label(frame_graph, text="EXIT Max (€):").grid(row=1, column=0, padx=5, pady=5)
entry_max = tk.Entry(frame_graph)
entry_max.grid(row=1, column=1, padx=5, pady=5)
'''
# Frame for iterative graph (EXIT Min and EXIT Max fields)
frame_graph = tk.Frame(root, padx=10, pady=10)
tk.Label(frame_graph, text="EXIT Min (€):").grid(row=0, column=0, padx=5, pady=5)

entry_min = tk.Entry(frame_graph)
entry_min.grid(row=0, column=1, padx=5, pady=5)
entry_min.bind("<FocusOut>", lambda event: format_exit_value(event, entry_min))  # 🔁 format

tk.Label(frame_graph, text="EXIT Max (€):").grid(row=1, column=0, padx=5, pady=5)

entry_max = tk.Entry(frame_graph)
entry_max.grid(row=1, column=1, padx=5, pady=5)
entry_max.bind("<FocusOut>", lambda event: format_exit_value(event, entry_max))  # 🔁 format

if mode_var.get() == 2:
    frame_graph.pack(fill='x', padx=10, pady=10)
else:
    frame_graph.pack_forget()

# Button to execute calculation
btn_calc = tk.Button(root, text="Calculate", command=calculate)
btn_calc.pack(pady=10)

# RESET button
btn_reset = tk.Button(root, text="Reset", command=reset_app, fg="darkblue")
btn_reset.pack(pady=5)

# GUIDE button
btn_help = tk.Button(root, text="Guide ℹ️", command=show_guide)
btn_help.pack(pady=5)



root.mainloop()
