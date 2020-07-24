# Leader_Likeability
A data project to calculate seat projections for different leader likeability values

## Method

The British Election Study releases waves of surveys, usually once a year or multiple times a year in election years. Wave 19 was released shortly after the 2019 election, and you can find the data here: https://www.britishelectionstudy.com/data-object/wave-19-of-the-2014-2023-british-election-study-internet-panel/

The study, among other things, asked interviewees their opinions on then-party leaders, as well as their opinions on Starmer, Davey and Moran. Specifically, the interviewees were asked to rate each leader out of 10.

The first step (in likeability.py) is to process this data into a regional breakdown. For each respondent, their region is noted (South-East, Wales, East etc..), as well as the party they voted for and their opinion on each leader. This is aggregated into a likeability Json, whose structure takes the following form:

Region (eg South-West)
	
	Party Voted (eg Labour)
	
		Leader Likeability (eg Farage)
			
			(Sum Likeability, Total Weight)
			
By later dividing the sum likeability by the total weight, the above example tells us what the average Labour voter in the South-West thinks of Farage. The total weight is used instead of the number of respondants, and this is based on the YouGov weighting algorithm, provided in the wave 19 data. This is repeated for every combination of region, party voted and leader opinion in order to get a complete likeability matrix. 

The next step (in constituency_correlations.py) is to go through the results of the 2019 election, as provided by the House of Commons library: https://commonslibrary.parliament.uk/research-briefings/cbp-8749/

For each constituency, the "average likeability" for each leader is calculated by considering vote shares. 

For example, we can say that "West Placeshire" in the North-West voted 45% Conservative, 35% Labour and 20% Liberal Democrat. The average Conservative voter in the North-West gave Swinson a 3/10. The average Labour voter gave a 4/10 and the average Liberal Democrat gave 7/10. Therefore, the average likeability in West Placeshire is the weighted average of these, 4.15/10

Then, we can scatter these constituencies on graphs which plot the vote share of the party versus the likeability of the leader. 

For example, in London, Swinson's various likeabilities netted her the following vote shares:

![Liberal Democrat vote share in London constituencies mapped against Jo Swinson's likeability. Constituencies are coloured by their 2019 result.](https://i.imgur.com/0ldUkLe.png)

These measurements can be repeated for each region, for each leader, to get 68 other such scatter graphs, which you can view here: https://imgur.com/a/b2o5Hey

Using the same correlation equations (y = mx + c), we can recalculate each constituency's likeability for Starmer, Moran and Davey in order to get the implied voter share for their parties if they were leader

Of course, from the above graph you can see that if hypothetically Davey found himself in a London constituency where his likeability was below 2.5, he would net himself a negative vote share due to being below the x-intercept, which is obviously impossible. 

To combat this, the raw predicted projections were compared to the actual 2019 results, in order to get a linear likeability offset for each constituency. For example the prediction in, say, "North Placedon" might predict a vote share of -0.05, but the real vote share was actually +0.07, so the offset here is +0.12. 

Then, the model was reapplied with these offsets in order to get two "base" scenarios to work from - one where Davey leads the LibDems and one where Moran does. Starmer, Johnson, Sturgeon etc are all assumed to be around in 2024 so their likeabilities were reused. 

There was an obvious problem. Starmer was far too popular after the election, in the context of Corbyn, and Davey/Moran were quite similar to Swinson. The raw base scenario predicted a Labour landslide on the scale of 500 or so seats. During the course of a campaign this is obviously very unrealistic. The best way to combat this was to apply a linear swing from the top down (calculate_linear_swing.py) based upon desired party vote shares. 

This produced csv files similar to the original 2019 election results as provided by the HoC Library. These CSV files were mapped on Flourish.

The likeability visualisations were mapped using the optional PrintLikeabilityCsv config parameter in constituency_correlations. The likeability comparison visualisation data was calculated in compare_likeability.py. The projection comparison between leaders was calculated using compare_results.py.


## Flourish Visualisations

All visualisations were created with Flourish Studio: https://flourish.studio/

### Absolute Likeabilities

Davey: https://public.flourish.studio/visualisation/3206063/

Moran: https://public.flourish.studio/visualisation/3206065/

### Relative Likeabilities

Davey/Moran All: https://public.flourish.studio/visualisation/3206298/

Davey/Moran Targets: https://public.flourish.studio/visualisation/3208818/

Davey/Johnson All: https://public.flourish.studio/visualisation/3278874/

Davey/Johnson Targets: https://public.flourish.studio/visualisation/3209419/

Moran/Johnson All: https://public.flourish.studio/visualisation/3278847/

Moran/Johnson Targets: https://public.flourish.studio/visualisation/3209604/

Davey/Starmer All: https://public.flourish.studio/visualisation/3209632/

Davey/Starmer Targets: https://public.flourish.studio/visualisation/3278711/

Moran/Starmer All: https://public.flourish.studio/visualisation/3209693/

Moran/Starmer Targets: https://public.flourish.studio/visualisation/3278833/

### Scenarios

#### Aggregates

Aggregate, Davey, Projection: https://public.flourish.studio/visualisation/3258420/

Aggregate, Davey, Second: https://public.flourish.studio/visualisation/3258520/

Aggregate, Moran, Projection: https://public.flourish.studio/visualisation/3258526/

Aggregate, Moran, Second: https://public.flourish.studio/visualisation/3258560/

Aggregate, Comparison, Projection: https://public.flourish.studio/visualisation/3258582/

Aggregate, Comparison, Second: https://public.flourish.studio/visualisation/3258605/

#### Scenario 1

Scenario 1, Davey, Projection: https://public.flourish.studio/visualisation/3234643/

Scenario 1, Davey, Second: https://public.flourish.studio/visualisation/3234653/

Scenario 1, Moran, Projection: https://public.flourish.studio/visualisation/3234660/

Scenario 1, Moran, Second: https://public.flourish.studio/visualisation/3234675/

Scenario 1, Comparison, Projection: https://public.flourish.studio/visualisation/3236007/

Scenario 1, Comparison, Second: https://public.flourish.studio/visualisation/3236012/

#### Scenario 2

Scenario 2, Davey, Projection: https://public.flourish.studio/visualisation/3234683/ 

Scenario 2, Davey, Second: https://public.flourish.studio/visualisation/3234694/ 

Scenario 2, Moran, Projection: https://public.flourish.studio/visualisation/3234702/

Scenario 2, Moran, Second: https://public.flourish.studio/visualisation/3234714/ 

Scenario 2, Comparison, Projection: https://public.flourish.studio/visualisation/3236022/ 

Scenario 2, Comparison, Second: https://public.flourish.studio/visualisation/3236032/

#### Scenario 3

Scenario 3, Davey, Projection: https://public.flourish.studio/visualisation/3235165/ 

Scenario 3, Davey, Second: https://public.flourish.studio/visualisation/3235184/ 

Scenario 3, Moran, Projection: https://public.flourish.studio/visualisation/3235190/ 

Scenario 3, Moran, Second: https://public.flourish.studio/visualisation/3235216/ 

Scenario 3, Comparison, Projection: https://public.flourish.studio/visualisation/3236043/ 

Scenario 3, Comparison, Second: https://public.flourish.studio/visualisation/3236052/ 

#### Scenario 4

Scenario 4, Davey, Projection: https://public.flourish.studio/visualisation/3235222/

Scenario 4, Davey, Second: https://public.flourish.studio/visualisation/3235331/

Scenario 4, Moran, Projection: https://public.flourish.studio/visualisation/3235335/

Scenario 4, Moran, Second: https://public.flourish.studio/visualisation/3235514/ 

Scenario 4, Comparison, Projection: https://public.flourish.studio/visualisation/3236064/

Scenario 4, Comparison, Second: https://public.flourish.studio/visualisation/3236075/

#### Scenario 5

Scenario 5, Davey, Projection: https://public.flourish.studio/visualisation/3235522/

Scenario 5, Davey, Second: https://public.flourish.studio/visualisation/3235535/

Scenario 5, Moran, Projection: https://public.flourish.studio/visualisation/3235545/

Scenario 5, Moran, Second: https://public.flourish.studio/visualisation/3235564/ 

Scenario 5, Comparison, Projection: https://public.flourish.studio/visualisation/3236079/ 

Scenario 5, Comparison, Second: https://public.flourish.studio/visualisation/3236085/ 

#### Scenario 6

Scenario 6, Davey, Projection: https://public.flourish.studio/visualisation/3235582/

Scenario 6, Davey, Second: https://public.flourish.studio/visualisation/3235590/

Scenario 6, Moran, Projection: https://public.flourish.studio/visualisation/3235599/ 

Scenario 6, Moran, Second: https://public.flourish.studio/visualisation/3235605/ 

Scenario 6, Comparison, Projection: https://public.flourish.studio/visualisation/3236087/

Scenario 6, Comparison, Second: https://public.flourish.studio/visualisation/3236100/ 

#### Scenario 7

Scenario 7, Davey, Projection: https://public.flourish.studio/visualisation/3235647/

Scenario 7, Davey, Second: https://public.flourish.studio/visualisation/3235669/

Scenario 7, Moran, Projection: https://public.flourish.studio/visualisation/3235684/ 

Scenario 7, Moran, Second: https://public.flourish.studio/visualisation/3235698/ 

Scenario 7, Comparison, Projection: https://public.flourish.studio/visualisation/3236103/

Scenario 7, Comparison, Second: https://public.flourish.studio/visualisation/3236114/

#### Scenario 8

Scenario 8, Davey, Projection: https://public.flourish.studio/visualisation/3235705/

Scenario 8, Davey, Second: https://public.flourish.studio/visualisation/3235754/

Scenario 8, Moran, Projection: https://public.flourish.studio/visualisation/3235772/

Scenario 8, Moran, Second: https://public.flourish.studio/visualisation/3235793/ 

Scenario 8, Comparison, Projection: https://public.flourish.studio/visualisation/3236121/

Scenario 8, Comparison, Second: https://public.flourish.studio/visualisation/3236127/

#### Scenario 9

Scenario 9, Davey, Projection: https://public.flourish.studio/visualisation/3235797/

Scenario 9, Davey, Second: https://public.flourish.studio/visualisation/3235810/ 

Scenario 9, Moran, Projection: https://public.flourish.studio/visualisation/3235818/ 

Scenario 9, Moran, Second: https://public.flourish.studio/visualisation/3235825/ 

Scenario 9, Comparison, Projection: https://public.flourish.studio/visualisation/3236132/ 

Scenario 9, Comparison, Second: https://public.flourish.studio/visualisation/3236143/ 

#### Scenario 10

Scenario 10, Davey, Projection: https://public.flourish.studio/visualisation/3235829/ 

Scenario 10, Davey, Second: https://public.flourish.studio/visualisation/3235845/ 

Scenario 10, Moran, Projection: https://public.flourish.studio/visualisation/3235858/ 

Scenario 10, Moran, Second: https://public.flourish.studio/visualisation/3235861/ 

Scenario 10, Comparison, Projection: https://public.flourish.studio/visualisation/3236162/ 

Scenario 10, Comparison, Second: https://public.flourish.studio/visualisation/3236177/ 

#### Scenario 11

Scenario 11, Davey, Projection: https://public.flourish.studio/visualisation/3235871/

Scenario 11, Davey, Second: https://public.flourish.studio/visualisation/3235880/ 

Scenario 11, Moran, Projection: https://public.flourish.studio/visualisation/3235889/ 

Scenario 11, Moran, Second: https://public.flourish.studio/visualisation/3235898/ 

Scenario 11, Comparison, Projection: https://public.flourish.studio/visualisation/3236183/ 

Scenario 11, Comparison, Second: https://public.flourish.studio/visualisation/3236190/ 

#### Scenario 12

Scenario 12, Davey, Projection: https://public.flourish.studio/visualisation/3235912/

Scenario 12, Davey, Second: https://public.flourish.studio/visualisation/3235918/ 

Scenario 12, Moran, Projection: https://public.flourish.studio/visualisation/3235921/ 

Scenario 12, Moran, Second: https://public.flourish.studio/visualisation/3235940/ 

Scenario 12, Comparison, Projection: https://public.flourish.studio/visualisation/3236198/

Scenario 12, Comparison, Second: https://public.flourish.studio/visualisation/3236202/ 