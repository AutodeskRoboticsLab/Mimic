MODULE MainModule
	! Pose variables
	CONST num NUMPOSES := {};
	CONST jointtarget poses{{NUMPOSES}} :=
    [
{}
    ];
	! Main routine
	PROC main()
		ConfL\Off;
		SingArea\Wrist;
		! Go to start position
        MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		! Go to programmed positions
		FOR i FROM 1 TO NUMPOSES DO
			MoveAbsJ poses{{i}}, v100, fine, tool0;
		ENDFOR
		! Go to end position
		MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		Stop;
	ENDPROC
ENDMODULE
