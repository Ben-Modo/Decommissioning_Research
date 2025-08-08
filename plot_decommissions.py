import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data (assuming the notebook has already processed it)
df_gas = pd.read_excel('/Users/benkitching-morley//Downloads/Global-Oil-and-Gas-Plant-Tracker-GOGPT-January-2025.xlsx', sheet_name='Gas & Oil Units')
df_coal = pd.read_excel('/Users/benkitching-morley//Downloads/Global-Coal-Plant-Tracker-January-2025.xlsx', sheet_name='Units')

# Process gas data
df_gas = df_gas[["Plant name", "Unit name", "Country/Area", "Status", "Fuel", "CHP", "Capacity (MW)", "Conversion from/replacement of (fuel)", "Conversion to (fuel)", "Start year", "Retired year", "Planned retire"]]

# Process coal data  
df_coal = df_coal.rename(columns={
    "Plant Name": "Plant name",
    "Planned retirement": "Planned retire", 
    "Coal type": "Fuel",
})
df_coal = df_coal[["Plant name", "Unit name", "Country/Area", "Status", "Fuel", "Capacity (MW)", "Conversion to (fuel)", "Start year", "Retired year", "Planned retire"]]

# Filter both coal and gas data to European countries
european_countries = [
    "Austria", "Belgium", "Czech Republic", "Czechia", "Denmark", 
    "France", "Germany", "Ireland", "Luxembourg", "Netherlands",
    "Norway", "Poland", "Portugal", "Spain", "Sweden", "Switzerland", "United Kingdom"
]

df_coal = df_coal[df_coal["Country/Area"].isin(european_countries)]
df_gas = df_gas[df_gas["Country/Area"].isin(european_countries)]

# All German coal to be decommissioned by 2037
df_coal["Planned retire"] = df_coal["Planned retire"].where(
    np.logical_or(
        np.logical_or(
            df_coal["Planned retire"].notna(),
            df_coal["Country/Area"] != "Germany"
        ),
        df_coal["Status"] != "operating"
    ),
    2037,
)

# Create retirement datasets - only include retirements from 2025 onwards
retirements_gas = df_gas[(df_gas["Planned retire"].notna()) & (df_gas["Planned retire"] >= 2025)].groupby(["Country/Area", "Fuel", "CHP", "Planned retire"])["Capacity (MW)"].sum().reset_index()
retirements_coal = df_coal[(df_coal["Planned retire"].notna()) & (df_coal["Planned retire"] >= 2025)].groupby(["Country/Area", "Fuel", "Planned retire"])["Capacity (MW)"].sum().reset_index()

# Prepare data for cumulative plotting
gas_by_country_year = retirements_gas.groupby(["Country/Area", "Planned retire"])["Capacity (MW)"].sum().reset_index()
gas_by_country_year["Plant Type"] = "Gas"

coal_by_country_year = retirements_coal.groupby(["Country/Area", "Planned retire"])["Capacity (MW)"].sum().reset_index() 
coal_by_country_year["Plant Type"] = "Coal"

# Combine datasets
all_retirements = pd.concat([coal_by_country_year, gas_by_country_year], ignore_index=True)

# Get all years and countries for the plot
min_year = 2025  # Start counting from 2025
max_year = int(all_retirements["Planned retire"].max())
years = list(range(min_year, max_year + 1))  # Create complete year range
countries = sorted(all_retirements["Country/Area"].unique())

# Create cumulative data for each country and plant type
def create_cumulative_data(plant_type):
    data = all_retirements[all_retirements["Plant Type"] == plant_type]
    cumulative_by_country = {}
    
    for country in countries:
        country_data = data[data["Country/Area"] == country]
        cumulative = []
        cumsum = 0
        
        for year in years:
            year_capacity = country_data[country_data["Planned retire"] == year]["Capacity (MW)"].sum()
            cumsum += year_capacity
            cumulative.append(cumsum / 1000)  # Convert MW to GW
        
        cumulative_by_country[country] = cumulative
    
    return cumulative_by_country

# Create cumulative data for both plant types
coal_cumulative = create_cumulative_data("Coal")
gas_cumulative = create_cumulative_data("Gas")

# Create the stacked area plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

# Colors for countries
colors = plt.cm.Set3(np.linspace(0, 1, len(countries)))
country_colors = dict(zip(countries, colors))

# Plot Coal
bottom_coal = np.zeros(len(years))
for country in countries:
    if max(coal_cumulative[country]) > 0:  # Only plot if country has retirements
        ax1.fill_between(years, bottom_coal, bottom_coal + coal_cumulative[country], 
                        label=country, alpha=0.8, color=country_colors[country])
        bottom_coal += coal_cumulative[country]

ax1.set_title('Cumulative Coal Plant Decommissions by Country', fontsize=14, fontweight='bold')
ax1.set_xlabel('Year')
ax1.set_ylabel('Cumulative Capacity Decommissioned (GW)')
ax1.legend(loc='upper left', fontsize=8)
ax1.grid(True, alpha=0.3)

# Plot Gas  
bottom_gas = np.zeros(len(years))
for country in countries:
    if max(gas_cumulative[country]) > 0:  # Only plot if country has retirements
        ax2.fill_between(years, bottom_gas, bottom_gas + gas_cumulative[country],
                        label=country, alpha=0.8, color=country_colors[country])
        bottom_gas += gas_cumulative[country]

ax2.set_title('Cumulative Gas Plant Decommissions by Country', fontsize=14, fontweight='bold')
ax2.set_xlabel('Year')
ax2.set_ylabel('Cumulative Capacity Decommissioned (GW)')
ax2.legend(loc='upper left', fontsize=8)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Print summary statistics
print(f"Total countries with planned retirements: {len(countries)}")
print(f"Year range: {min(years)} to {max(years)}")
print(f"Total planned coal capacity retirement: {sum([max(coal_cumulative[c]) for c in countries]):,.1f} GW")
print(f"Total planned gas capacity retirement: {sum([max(gas_cumulative[c]) for c in countries]):,.1f} GW")