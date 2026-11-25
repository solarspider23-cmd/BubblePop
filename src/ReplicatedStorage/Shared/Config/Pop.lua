-- How popping feels. Tune these after play-testing.
return {
	-- Clicking with the tool
	popTime = 0.56, -- seconds from click to POP (the press/squeeze). Upgrades will lower this.
	reach = 9, -- studs from the camera the tool can poke
	aimRadius = 0.25, -- aim forgiveness: the crosshair picks a bubble this close to its line
	stickyRadius = 0.75, -- holding on a popped spot moves on to a neighbour this close
	reachSlack = 5, -- extra distance the server allows (camera vs body position, lag)
	timeTolerance = 0.12, -- the server accepts pops this much faster than popTime (lag)

	-- Walking over floor wrap
	stompRadius = 1.1, -- floor bubbles this close (sideways) to your body pop under you
	stompSlack = 1.6, -- extra sideways distance the server allows
	stompMaxPerSecond = 40,

	-- Popped bubbles grow back? Off: a run ends when the whole room is cleared (timed).
	regrow = false,
	regrowSeconds = 40, -- if regrow is on: seconds until a popped bubble grows back

	-- Press animation
	squashHeight = 0.45, -- the bubble's height at the end of the press (1 = full)
	squashBulge = 1.14, -- how much it bulges sideways at the end of the press
	reachPhase = 0.28, -- part of popTime the stick takes to travel to the bubble
}
