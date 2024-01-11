## Main ideas of improvement
- [ ] download wave data as well in order to classify the environment (soft, medium or harsh for exemple), to increase precision on the calculation of the pipes/mooring
- [ ] for each region, save the zone considered on the world map as an image stored and in the related folder
- [ ] consider the risk factor : mooring and pipe represent less than 50% of the total cost, but they have 90% of the risk
- [ ] regarding the pipe cost calculation, divide it into material, fabrication, transport, deployment costs.
- [ ] estimate uncertainties to the various cost calculations, based on extensive literature review or input data from companies.

## Parameters and constants than can be redefined more accurately

- [ ] rho_WW : can be replaced by calculated value from Equation of seawater : need to download salinity as well in Copernicus
- [ ] roughness_pipe : litterature review to make to confirm a value
- [ ] length_CW_inlet : maybe sometimes it can be cheaper to pump at a lower depth with a smaller pipe
- [ ] discharged pipe length : should be defined
- [ ] max_p : litterature review and/or calculation based on max pump NPSH to make to confirm a value