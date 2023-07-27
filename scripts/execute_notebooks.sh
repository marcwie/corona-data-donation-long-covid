to_execute=(
    '1.01-plot_example_timeseries.ipynb'
    '1.02-plot_average_trajectories.ipynb'
    '1.03-plot_distributions_of_vital_changes.ipynb'
    '1.04-plot_frequencies_of_extreme_vitals.ipynb'
    '1.05-table_with_basic_user_demographics.ipynb'
    '1.06-plot_positive_pcr_tests_per_month.ipynb'
    '1.07-plot_time_between_vaccination_and_infection.ipynb'
    '1.08-plot_comparison_age_groups_datenspende_and_overall_population.ipynb'
    '1.09-plot_example_of_computing_anomalies.ipynb'
    '1.10-plot-qq-plots.ipynb'
    '1.11-plot-average-trajectories-as-boxplots.ipynb'
)

cd notebooks

for filename in ${to_execute[@]}
do
	echo $filename
	poetry run jupyter nbconvert --to=python --output=out $filename
	poetry run python out.py
done

rm out.py
