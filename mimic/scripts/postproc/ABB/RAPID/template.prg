MODULE MainModule
	! Main routine
	PROC main()
		ConfL\Off;
		SingArea\Wrist;
		! Go to start position
        MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		! Go to programmed positions
{}
		! Go to end position
		MoveAbsJ [[0, 0, 0, 0, 0, 0], [9E9, 9E9, 9E9, 9E9, 9E9, 9E9]], v100, fine, tool0;
		Stop;
	ENDPROC
ENDMODULE
