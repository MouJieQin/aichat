<template>
    <!-- By Sam Herbert (@sherb), for everyone. More @ http://goo.gl/7AJzbL -->
    <svg width="35" height="35" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" stroke="var(--puff-loader-color)">
        <g fill="none" fill-rule="evenodd" stroke-width="2">
            <circle cx="22" cy="22" r="1">
                <animate attributeName="r" begin="0s" dur="5s" values="1; 20" calcMode="spline" keyTimes="0; 1"
                    keySplines="0.165, 0.84, 0.44, 1" repeatCount="indefinite" />
                <animate attributeName="stroke-opacity" begin="0s" dur="5s" values="1; 0" calcMode="spline"
                    keyTimes="0; 1" keySplines="0.3, 0.61, 0.355, 1" repeatCount="indefinite" />
            </circle>
            <circle cx="22" cy="22" r="1">
                <animate attributeName="r" begin="-2.5s" dur="5s" values="1; 20" calcMode="spline" keyTimes="0; 1"
                    keySplines="0.165, 0.84, 0.44, 1" repeatCount="indefinite" />
                <animate attributeName="stroke-opacity" begin="-2.5s" dur="5s" values="1; 0" calcMode="spline"
                    keyTimes="0; 1" keySplines="0.3, 0.61, 0.355, 1" repeatCount="indefinite" />
            </circle>
        </g>
    </svg>
</template>

