node(label: 'raspberrypi') {
    properties([
            disableConcurrentBuilds(),
            durabilityHint(hint: 'PERFORMANCE_OPTIMIZED')
        ])

    // --- configuration for an arch-indep package ---

    // The distributions we build on
    def build_dist_list = [
      "bullseye"
    ]

    // The distribution/architecture combinations we test-install on.
    def test_dist_arch_list = [
      ["bullseye", "armhf"]
    ]

    // The list of packages to test-install, in the correct order to install.
    def test_package_list = ["piaware-wifi-scan", "piawware-configurator"]

    // --- implementation ---

    def srcdir = "${WORKSPACE}/src"

    stage("Checkout") {
        sh "rm -fr ${srcdir}"
        sh "mkdir ${srcdir}"
        dir(srcdir) {
            checkout scm
        }
    }

    def resultdirs = [:]
    for (int i = 0; i < build_dist_list.size(); ++i) {
        def dist = build_dist_list[i]

        String pkgdir = "pkg-${dist}"
        stage("Prepare source for ${dist}") {
            sh "rm -fr ${pkgdir}"
            sh "${srcdir}/prepare-build.sh ${dist} ${pkgdir}"
        }

        def resultdir = "results-${dist}"
        resultdirs[dist] = resultdir

        stage("Build for ${dist}") {
          sh "rm -fr ${resultdir}"
          sh "mkdir -p ${resultdir}"
          dir(pkgdir) {
            sh "DIST=${dist} BRANCH=${env.BRANCH_NAME} pdebuild --use-pdebuild-internal --debbuildopts -b --buildresult ${WORKSPACE}/${resultdir}"
          }
          archiveArtifacts artifacts: "${resultdir}/*.deb", fingerprint: true
        }
    }

    for (int i = 0; i < test_dist_arch_list.size(); ++i) {
      def dist_and_arch = test_dist_arch_list[i]
      def dist = dist_and_arch[0]
      def arch = dist_and_arch[1]
      def resultdir = resultdirs[dist]

      def test_debs = ""
      for (int j = 0; j < test_package_list.size(); ++j) {
        test_debs += "${resultdir}/${test_package_list[j]}_*.deb "
      }

      stage("Test install on ${dist} (${arch})") {
        sh "BRANCH=${env.BRANCH_NAME} ARCH=${arch} /build/pi-builder/scripts/validate-packages.sh ${dist} ${test_debs}"
      }
    }

    stage("Deploy to internal repository") {
        for (int i = 0; i < build_dist_list.size(); ++i) {
            def dist = build_dist_list[i]
            def resultdir = resultdirs[dist]

            sh "/build/pi-builder/scripts/deploy.sh -distribution ${dist} -branch ${env.BRANCH_NAME} ${resultdir}/*.deb"
        }
    }
}
