/* ========================== STRUCTURES ============================ */


/* Binary semaphore */
typedef struct bsem {
    pthread_mutex_t mutex;
    pthread_cond_t   cond;
    int v;
} bsem;


/* Job */
typedef struct job{
    struct job*  prev;                   /* pointer to previous job   */
    void   (*function)(void* arg);       /* function pointer          */
    void*  arg;                          /* function's argument       */
} job;


/* Job queue */
typedef struct jobqueue{
    pthread_mutex_t rwmutex;             /* used for queue r/w access */
    job  *front;                         /* pointer to front of queue */
    job  *rear;                          /* pointer to rear  of queue */
    bsem *has_jobs;                      /* flag as binary semaphore  */
    int   len;                           /* number of jobs in queue   */
} jobqueue;


/* Thread */
typedef struct thread{
    int       id;                        /* friendly id               */
    pthread_t pthread;                   /* pointer to actual thread  */
    struct thpool_* thpool_p;            /* access to thpool          */
} thread;


/* Threadpool */
typedef struct thpool_{
    thread**   threads;                  /* pointer to threads        */
    volatile int num_threads_alive;      /* threads currently alive   */
    volatile int num_threads_working;    /* threads currently working */
    pthread_mutex_t  thcount_lock;       /* used for thread count etc */
    pthread_cond_t  threads_all_idle;    /* signal to thpool_wait     */
    jobqueue  jobqueue;                  /* job queue                 */
} thpool_;

/* ====================================================== */

typedef enum TL_STATE_E {
    TBL_INITED,
    TBL_USING,
    TBL_TIMEOUT1,
    TBL_TIMEOUT2,
    TBL_AGING
} TL_STATE_E;

typedef union IP_KEY_UN {
    struct {
        unsigned int uiIpv4SrcAddr;
        unsigned int uiIpv4DestAddr;
        unsigned int uiZeroPadding[6];
    } KEY_IPV4_S;

    struct {
        unsigned int uiIpv6SrcAddr[4];
        unsigned int uiIpv4DestAddr[4];
    } KEY_IPV6_S;

    struct {
        unsigned int uiGeneralKey[8];
    } KEY_GENERAL_S;
} IP_KEY_UN;

typedef struct QUEUE_NODE_S {
    /* hash key */
    IP_KEY_UN unIpTupleKey;
    unsigned long long uiiIdentifier;

    unsigned short usL4SrcPort;
    unsigned short usL4DestPort;
    unsigned char ucProtocol;
    unsigned char ucIpVersion;

    /* hash payload */
    unsigned long long uiiRxSysTicks; // system ticks of recv pakcet
} QUEUE_NODE_S;

typedef struct HASH_HEADER_S {
    HASH_TABLE_S *pstTable;
    spinlock_t stLock;
    unsigned long long uiiStartTicks;
    TL_STATE_E eTableState;
} HASH_HEADER_S;

typedef struct HASH_TABLE_S {
    unsigned long long ulSize; // The size of the hash table
    unsigned long long (*pfHash)(const void *); // A pointer to a hash function
    HASH_LIST_S *pstBckt; // A pointer to the bucket list of the hash table
} HASH_TABLE_S;

typedef struct tagDL_NODE {
    struct tagDL_NODE *pstNext; // A pointer to the next node in the doubly linked list
    struct tagDL_NODE **ppstPre; // A pointer to the previous node's pointer in the doubly linked list
} DL_HEAD_S;

typedef DL_HEAD_S HASH_LIST_S;
