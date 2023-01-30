to_execute=(
    '1.1-plot_example_timeseries.ipynb'
    '1.2-plot_average_trajectories.ipynb'
    '1.3-plot_distributions_of_vital_changes.ipynb'
    '1.4-plot_frequencies_of_extreme_vitals.ipynb'
    '1.5-table_with_basic_user_demographics.ipynb'
    '1.6-plot_positive_pcr_tests_per_month.ipynb'
    '1.7-plot_time_between_vaccination_and_infection.ipynb'
    '1.8-plot_comparison_age_groups_datenspende_and_overall_population.ipynb'
)

cd notebooks

for filename in ${to_execute[@]}
do
	echo $filename
	poetry run jupyter nbconvert --to=python --output=out $filename
	poetry run python out.py
done

rm out.py
